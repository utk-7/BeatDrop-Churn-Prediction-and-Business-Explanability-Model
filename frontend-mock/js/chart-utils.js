// BeatDrop Chart Utilities - SVG-based chart rendering

const ChartUtils = {
  // Render a horizontal bar chart (for churn drivers)
  renderHorizontalBarChart(container, data, options = {}) {
    const width = container.clientWidth || 600;
    const height = data.length * 40 + 40;
    const barHeight = 24;
    const maxValue = Math.max(...data.map(d => d.value));

    let svg = `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">`;

    data.forEach((item, i) => {
      const y = i * 40 + 10;
      const barWidth = (item.value / maxValue) * (width - 200);
      const color = item.color || '#2563eb';

      svg += `<text x="0" y="${y + barHeight / 2 + 4}" font-size="12" fill="#64748b" font-family="sans-serif">${item.label}</text>`;
      svg += `<rect x="180" y="${y}" width="${barWidth}" height="${barHeight}" rx="4" fill="${color}" opacity="0.8"/>`;
      svg += `<text x="${180 + barWidth + 8}" y="${y + barHeight / 2 + 4}" font-size="12" fill="#1e293b" font-family="sans-serif" font-weight="500">${item.value}%</text>`;
    });

    svg += '</svg>';
    container.innerHTML = svg;
  },

  // Render ROC curve as SVG
  renderROCCurve(container, curveData) {
    const width = container.clientWidth || 500;
    const height = 300;
    const padding = 50;
    const plotWidth = width - padding * 2;
    const plotHeight = height - padding * 2;

    const fprMin = Math.min(...curveData.fpr);
    const fprMax = Math.max(...curveData.fpr);
    const tprMin = Math.min(...curveData.tpr);
    const tprMax = Math.max(...curveData.tpr);

    const fprRange = fprMax - fprMin || 1;
    const tprRange = tprMax - tprMin || 1;

    function toX(fpr) { return padding + ((fpr - fprMin) / fprRange) * plotWidth; }
    function toY(tpr) { return height - padding - ((tpr - tprMin) / tprRange) * plotHeight; }

    let points = curveData.fpr.map((fpr, i) => `${toX(fpr)},${toY(curveData.tpr[i])}`).join(' ');

    let svg = `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">`;

    // Background
    svg += `<rect x="${padding}" y="${padding}" width="${plotWidth}" height="${plotHeight}" fill="#f8fafc" rx="4"/>`;

    // Diagonal reference line (random classifier)
    svg += `<line x1="${toX(0)}" y1="${toY(0)}" x2="${toX(1)}" y2="${toY(1)}" stroke="#cbd5e1" stroke-width="2" stroke-dasharray="6,4"/>`;

    // ROC Curve
    svg += `<polyline points="${points}" fill="none" stroke="#2563eb" stroke-width="3"/>`;
    svg += `<circle cx="${toX(curveData.fpr[curveData.fpr.length - 1])}" cy="${toY(curveData.tpr[curveData.tpr.length - 1])}" r="5" fill="#1d4ed8"/>`;

    // AUC label
    svg += `<text x="${padding + plotWidth / 2}" y="${padding - 10}" text-anchor="middle" font-size="13" fill="#64748b" font-family="sans-serif" font-weight="600">ROC Curve (AUC = ${curveData.auc || '0.92'})</text>`;

    // Axis labels
    svg += `<text x="${padding + plotWidth / 2}" y="${height - 8}" text-anchor="middle" font-size="11" fill="#64748b" font-family="sans-serif">False Positive Rate</text>`;
    svg += `<text x="15" y="${padding + plotHeight / 2}" text-anchor="middle" font-size="11" fill="#64748b" font-family="sans-serif" transform="rotate(-90, 15, ${padding + plotHeight / 2})">True Positive Rate</text>`;

    // Grid lines
    for (let i = 0; i <= 4; i++) {
      const x = padding + (i / 4) * plotWidth;
      const y = padding + (i / 4) * plotHeight;
      svg += `<line x1="${x}" y1="${padding}" x2="${x}" y2="${padding + plotHeight}" stroke="#e2e8f0" stroke-width="1"/>`;
      svg += `<line x1="${padding}" y1="${y}" x2="${padding + plotWidth}" y2="${y}" stroke="#e2e8f0" stroke-width="1"/>`;
      svg += `<text x="${x}" y="${height - 3}" text-anchor="middle" font-size="10" fill="#94a3b8">${(i / 4).toFixed(1)}</text>`;
      svg += `<text x="${padding - 8}" y="${y + 4}" text-anchor="end" font-size="10" fill="#94a3b8">${(i / 4).toFixed(1)}</text>`;
    }

    svg += '</svg>';
    container.innerHTML = svg;
  },

  // Render PR curve as SVG
  renderPRCurve(container, curveData) {
    const width = container.clientWidth || 500;
    const height = 300;
    const padding = 50;
    const plotWidth = width - padding * 2;
    const plotHeight = height - padding * 2;

    let points = curveData.recall.map((recall, i) => `${plotWidth * (1 - recall) + padding},${height - padding - curveData.precision[i] * plotHeight}`).join(' ');

    let svg = `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">`;

    svg += `<rect x="${padding}" y="${padding}" width="${plotWidth}" height="${plotHeight}" fill="#f8fafc" rx="4"/>`;

    // Baseline (precision = positive rate)
    svg += `<line x1="${padding}" y1="${height - padding - 0.35 * plotHeight}" x2="${padding + plotWidth}" y2="${height - padding - 0.35 * plotHeight}" stroke="#cbd5e1" stroke-width="2" stroke-dasharray="6,4"/>`;

    svg += `<polyline points="${points}" fill="none" stroke="#10b981" stroke-width="3"/>`;
    svg += `<circle cx="${padding}" cy="${height - padding - curveData.precision[0] * plotHeight}" r="5" fill="#059669"/>`;

    svg += `<text x="${padding + plotWidth / 2}" y="${padding - 10}" text-anchor="middle" font-size="13" fill="#64748b" font-family="sans-serif" font-weight="600">Precision-Recall Curve (PR AUC = ${curveData.pr_auc || '0.89'})</text>`;

    svg += `<text x="${padding + plotWidth / 2}" y="${height - 8}" text-anchor="middle" font-size="11" fill="#64748b" font-family="sans-serif">Recall</text>`;
    svg += `<text x="15" y="${padding + plotHeight / 2}" text-anchor="middle" font-size="11" fill="#64748b" font-family="sans-serif" transform="rotate(-90, 15, ${padding + plotHeight / 2})">Precision</text>`;

    for (let i = 0; i <= 4; i++) {
      const x = padding + (i / 4) * plotWidth;
      const y = padding + (i / 4) * plotHeight;
      svg += `<line x1="${x}" y1="${padding}" x2="${x}" y2="${padding + plotHeight}" stroke="#e2e8f0" stroke-width="1"/>`;
      svg += `<line x1="${padding}" y1="${y}" x2="${padding + plotWidth}" y2="${y}" stroke="#e2e8f0" stroke-width="1"/>`;
      svg += `<text x="${x}" y="${height - 3}" text-anchor="middle" font-size="10" fill="#94a3b8">${(1 - i / 4).toFixed(1)}</text>`;
      svg += `<text x="${padding - 8}" y="${y + 4}" text-anchor="end" font-size="10" fill="#94a3b8">${(i / 4).toFixed(1)}</text>`;
    }

    svg += '</svg>';
    container.innerHTML = svg;
  },

  // Render calibration plot as SVG (predicted vs actual)
  renderCalibrationPlot(container, calData) {
    const width = container.clientWidth || 500;
    const height = 300;
    const padding = 50;
    const plotWidth = width - padding * 2;
    const plotHeight = height - padding * 2;

    const maxVal = 1;
    const points = calData.map(d => `${padding + d.predicted * plotWidth},${height - padding - d.actual * plotHeight}`).join(' ');

    let svg = `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">`;

    svg += `<rect x="${padding}" y="${padding}" width="${plotWidth}" height="${plotHeight}" fill="#f8fafc" rx="4"/>`;

    // Perfect calibration line
    svg += `<line x1="${padding}" y1="${height - padding}" x2="${padding + plotWidth}" y2="${padding}" stroke="#10b981" stroke-width="2" stroke-dasharray="4,3"/>`;

    // Calibration curve
    svg += `<polyline points="${points}" fill="none" stroke="#2563eb" stroke-width="3"/>`;

    // Reference diagonal (random)
    svg += `<line x1="${padding}" y1="${height - padding}" x2="${padding + plotWidth}" y2="${padding}" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="2,2"/>`;

    // Data points
    calData.forEach(d => {
      const cx = padding + d.predicted * plotWidth;
      const cy = height - padding - d.actual * plotHeight;
      svg += `<circle cx="${cx}" cy="${cy}" r="4" fill="#2563eb" opacity="0.8"/>`;
    });

    svg += `<text x="${padding + plotWidth / 2}" y="${padding - 10}" text-anchor="middle" font-size="13" fill="#64748b" font-family="sans-serif" font-weight="600">Calibration Plot</text>`;
    svg += `<text x="${padding + plotWidth / 2}" y="${height - 8}" text-anchor="middle" font-size="11" fill="#64748b" font-family="sans-serif">Mean Predicted Probability</text>`;

    svg += `<text x="15" y="${padding + plotHeight / 2}" text-anchor="middle" font-size="11" fill="#64748b" font-family="sans-serif" transform="rotate(-90, 15, ${padding + plotHeight / 2})">Fraction of Positives</text>`;

    for (let i = 0; i <= 4; i++) {
      const x = padding + (i / 4) * plotWidth;
      svg += `<line x1="${x}" y1="${padding}" x2="${x}" y2="${padding + plotHeight}" stroke="#e2e8f0" stroke-width="1"/>`;
      svg += `<text x="${x}" y="${height - 3}" text-anchor="middle" font-size="10" fill="#94a3b8">${(i / 4).toFixed(1)}</text>`;

      const y = padding + (i / 4) * plotHeight;
      svg += `<text x="${padding - 8}" y="${y + 4}" text-anchor="end" font-size="10" fill="#94a3b8">${(i / 4).toFixed(1)}</text>`;
    }

    svg += '</svg>';
    container.innerHTML = svg;
  },

  // Render confusion matrix as SVG heatmap
  renderConfusionMatrix(container, matrix) {
    const labels = ['Pred Neg', 'Pred Pos'];
    const actualLabels = ['Actual Neg', 'Actual Pos'];
    const values = [
      [matrix.trueNegatives, matrix.falsePositives],
      [matrix.falseNegatives, matrix.truePositives]
    ];

    const cellMin = Math.min(...values.flat());
    const cellMax = Math.max(...values.flat());
    const cellRange = cellMax - cellMin || 1;

    function getColor(val) {
      const intensity = ((val - cellMin) / cellRange) * 0.8 + 0.1;
      if (val === cellMax) return `rgba(37, 99, 235, ${intensity})`;
      return `rgba(59, 130, 246, ${intensity * 0.5})`;
    }

    const svgW = 500;
    const svgH = 340;
    const cellW = 160;
    const cellH = 80;
    const startX = 120;
    const startY = 60;

    let svg = `<svg width="${svgW}" height="${svgH}" viewBox="0 0 ${svgW} ${svgH}" xmlns="http://www.w3.org/2000/svg">`;

    // Title
    svg += `<text x="${svgW / 2}" y="22" text-anchor="middle" font-size="13" fill="#64748b" font-family="sans-serif" font-weight="600">Confusion Matrix</text>`;

    // Actual labels
    svg += `<text x="87" y="${startY + cellH / 2 + 4}" text-anchor="middle" font-size="11" fill="#64748b" font-family="sans-serif">Actual Neg</text>`;
    svg += `<text x="87" y="${startY + 1.5 * cellH + 4}" text-anchor="middle" font-size="11" fill="#64748b" font-family="sans-serif">Actual Pos</text>`;

    // Cells
    for (let row = 0; row < 2; row++) {
      for (let col = 0; col < 2; col++) {
        const x = startX + col * cellW;
        const y = startY + row * cellH;
        svg += `<rect x="${x}" y="${y}" width="${cellW}" height="${cellH}" fill="${getColor(values[row][col])}" stroke="#e2e8f0" stroke-width="1"/>`;
        svg += `<text x="${x + cellW / 2}" y="${y + cellH / 2 - 6}" text-anchor="middle" font-size="12" fill="#1e293b" font-family="sans-serif" font-weight="600">${values[row][col].toLocaleString()}</text>`;

        const pct = values[row][col] / (matrix.trueNegatives + matrix.falsePositives + matrix.falseNegatives + matrix.truePositives) * 100;
        svg += `<text x="${x + cellW / 2}" y="${y + cellH / 2 + 12}" text-anchor="middle" font-size="10" fill="#64748b" font-family="sans-serif">${pct.toFixed(1)}%</text>`;
      }
    }

    // Predicted labels
    svg += `<text x="${startX + cellW / 2}" y="${startY + 2 * cellH + 18}" text-anchor="middle" font-size="11" fill="#64748b" font-family="sans-serif">Pred Neg</text>`;
    svg += `<text x="${startX + 1.5 * cellW + 20}" y="${startY + 2 * cellH + 18}" text-anchor="middle" font-size="11" fill="#64748b" font-family="sans-serif">Pred Pos</text>`;

    svg += '</svg>';
    container.innerHTML = svg;
  }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
  const app = window.app = new BeatDropApp();
});