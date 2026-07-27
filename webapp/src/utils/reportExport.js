import { jsPDF } from 'jspdf';

export function exportJsonReport(report) {
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'wallet-report.json';
  link.click();
  URL.revokeObjectURL(url);
}

export function exportPdfReport(report) {
  const doc = new jsPDF();
  doc.setFontSize(18);
  doc.text('Wallet Intelligence Report', 14, 20);
  doc.setFontSize(12);
  doc.text(`Portfolio score: ${report.portfolio_score ?? 0}/100`, 14, 36);
  doc.text(`Summary: ${report.summary || 'No summary available.'}`, 14, 48, { maxWidth: 180 });
  doc.text(`Recommendations: ${((report.recommendations || []).slice(0, 3)).join(' | ')}`, 14, 72, { maxWidth: 180 });
  doc.save('wallet-report.pdf');
}
