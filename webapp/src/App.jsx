import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Simulation from './pages/Simulation';
import Protection from './pages/Protection';
import Compare from './pages/Compare';
import WalletScanner from './pages/WalletScanner';
import Docs from './pages/Docs';
import About from './pages/About';
import './tokens.css';

const TITLES = {
  '/': 'Home',
  '/dashboard': 'Analysis Dashboard',
  '/simulation': 'Attack Simulation',
  '/protection': 'Protection Advisor',
  '/compare': 'Compare Tokens',
  '/wallet': 'Wallet Scanner',
  '/docs': 'API Documentation',
  '/about': 'About',
};

function PageWithLayout({ path, children }) {
  return <Layout title={TITLES[path] || 'Crypto Due Diligence'}>{children}</Layout>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<PageWithLayout path="/"><Home /></PageWithLayout>} />
        <Route path="/dashboard" element={<PageWithLayout path="/dashboard"><Dashboard /></PageWithLayout>} />
        <Route path="/simulation" element={<PageWithLayout path="/simulation"><Simulation /></PageWithLayout>} />
        <Route path="/protection" element={<PageWithLayout path="/protection"><Protection /></PageWithLayout>} />
        <Route path="/compare" element={<PageWithLayout path="/compare"><Compare /></PageWithLayout>} />
        <Route path="/wallet" element={<PageWithLayout path="/wallet"><WalletScanner /></PageWithLayout>} />
        <Route path="/docs" element={<PageWithLayout path="/docs"><Docs /></PageWithLayout>} />
        <Route path="/about" element={<PageWithLayout path="/about"><About /></PageWithLayout>} />
      </Routes>
    </BrowserRouter>
  );
}
