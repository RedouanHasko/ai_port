import React from "react";
import ThemeToggle from "./ThemeToggle";

interface HeaderProps {
  toggleSidebar: () => void;
}

const Header: React.FC<HeaderProps> = ({ toggleSidebar }) => {
  return (
    <header className="flex justify-between items-center p-4 bg-gray-300 dark:bg-gray-800">
      <button
        onClick={toggleSidebar}
        className="p-2 rounded text-gray-700 dark:text-white"
      >
        ☰
      </button>
      <h1 className="text-xl font-bold text-gray-800 dark:text-white">Hasko</h1>
      <ThemeToggle />
    </header>
  );
};

export default Header;
