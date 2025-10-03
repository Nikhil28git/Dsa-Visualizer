import React from 'react';
import Navbar from './Navbar';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const handleSidebarToggle = () => {
    // This is now handled by the navbar dropdowns on desktop
    // On mobile, we could implement a mobile menu if needed
  };

  return (
    <div className="d-flex flex-column min-vh-100">
      {/* Navbar */}
      <Navbar onSidebarToggle={handleSidebarToggle} />

      {/* Main Content */}
      <main className="flex-grow-1">
        {children}
      </main>
    </div>
  );
};

export default Layout;
