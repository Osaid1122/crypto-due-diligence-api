export default function ChainLogo({ chain, size = 20, className = '' }) {
  if (chain === 'solana') {
    return <svg className={className} width={size} height={size} viewBox="0 0 32 32" aria-label="Solana logo" role="img">
      <defs><linearGradient id="solana-gradient" x1="3" y1="29" x2="29" y2="3" gradientUnits="userSpaceOnUse"><stop stopColor="#9945FF" /><stop offset=".48" stopColor="#14F195" /><stop offset="1" stopColor="#00C2FF" /></linearGradient></defs>
      <path fill="url(#solana-gradient)" d="M7.1 21.3c.3-.3.7-.5 1.1-.5h20.1c.7 0 1 .9.5 1.4l-4 4c-.3.3-.7.5-1.1.5H3.6c-.7 0-1-.9-.5-1.4l4-4ZM7.1 5.5c.3-.3.7-.5 1.1-.5h20.1c.7 0 1 .9.5 1.4l-4 4c-.3.3-.7.5-1.1.5H3.6c-.7 0-1-.9-.5-1.4l4-4Zm17.7 7.9c.3-.3.7-.5 1.1-.5h2.4c.7 0 1 .9.5 1.4l-4 4c-.3.3-.7.5-1.1.5H3.6c-.7 0-1-.9-.5-1.4l4-4c.3-.3.7-.5 1.1-.5h16.6Z" />
    </svg>;
  }
  if (chain === 'xlayer') {
    return <svg className={className} width={size} height={size} viewBox="0 0 32 32" aria-label="X Layer logo" role="img"><rect width="32" height="32" rx="8" fill="#111827" /><path d="m8 8 16 16M24 8 8 24" stroke="#fff" strokeWidth="3" strokeLinecap="round" /><circle cx="16" cy="16" r="3" fill="#2DD4BF" /></svg>;
  }
  return <svg className={className} width={size} height={size} viewBox="0 0 32 32" aria-label="Ethereum logo" role="img">
    <path fill="#8A92B2" d="m16 2-8.4 14L16 20.9 24.4 16 16 2Z" /><path fill="#62688F" d="m16 2v18.9l8.4-4.9L16 2Z" /><path fill="#8A92B2" d="m16 30-8.4-11.5L16 23.4V30Z" /><path fill="#62688F" d="m16 30v-6.6l8.4-4.9L16 30Z" /><path fill="#454A75" d="m16 20.9-8.4-4.9L16 12v8.9Z" /><path fill="#62688F" d="M16 12v8.9l8.4-4.9L16 12Z" />
  </svg>;
}
