import React, { useState } from "react";
import { FaEdit, FaTrash, FaTimes } from "react-icons/fa";

interface SidebarProps {
  chats: {
    id: number;
    name: string;
    date: string;
    messages: { text: string; isUser: boolean }[];
  }[];
  onSelectChat: (chatId: number) => void;
  onDeleteChat: (chatId: number) => void;
  onAddChat: () => void;
  onRenameChat: (chatId: number, newName: string) => void;
  isOpen: boolean;
  selectedChatId: number | null;
  onCloseSidebar: () => void; // New prop to handle closing the sidebar
}

const Sidebar: React.FC<SidebarProps> = ({
  chats,
  onSelectChat,
  onDeleteChat,
  onAddChat,
  onRenameChat,
  isOpen,
  selectedChatId,
  onCloseSidebar,
}) => {
  const [editingChatId, setEditingChatId] = useState<number | null>(null);
  const [newChatName, setNewChatName] = useState("");

  const startEditingChat = (chatId: number, currentName: string) => {
    setEditingChatId(chatId);
    setNewChatName(currentName);
  };

  const handleSaveChatName = (chatId: number) => {
    onRenameChat(chatId, newChatName);
    setEditingChatId(null); // Exit editing mode
    setNewChatName("");
  };

  const handleCancelEdit = () => {
    setEditingChatId(null);
    setNewChatName("");
  };

  return (
    <div
      className={`fixed top-0 left-0 h-full bg-gray-100 dark:bg-gray-900 transform ${
        isOpen ? "translate-x-0 w-full md:w-64" : "-translate-x-full w-0"
      } transition-transform duration-300 shadow-lg overflow-y-auto z-50`}
    >
      {isOpen && (
        <>
          {/* Close Button for Mobile */}
          <div className="flex justify-between items-center p-4">
            <h2 className="text-lg font-bold text-black dark:text-white">
              Chats
            </h2>
            <button
              onClick={onCloseSidebar}
              className="md:hidden p-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100"
            >
              <FaTimes size={24} />
            </button>
          </div>
          <button
            onClick={onAddChat}
            className="px-4 py-2 bg-blue-500 text-white rounded m-4 w-[calc(100%-2rem)] hover:bg-blue-600"
          >
            New Chat
          </button>
          <ul>
            {chats.map((chat) => (
              <li
                key={chat.id}
                onClick={() => {
                  onSelectChat(chat.id);
                  // Close the sidebar on mobile when a chat is selected
                  if (window.innerWidth < 768) {
                    onCloseSidebar();
                  }
                }}
                className={`p-2 flex justify-between items-center cursor-pointer rounded-md ${
                  chat.id === selectedChatId
                    ? "bg-blue-500 text-white"
                    : "hover:bg-gray-200 dark:hover:bg-gray-700 text-black dark:text-white"
                }`}
              >
                {editingChatId === chat.id ? (
                  // Inline editing view
                  <div className="flex items-center w-full">
                    <input
                      type="text"
                      value={newChatName}
                      onChange={(e) => setNewChatName(e.target.value)}
                      className="p-1 text-black dark:text-white bg-gray-200 dark:bg-gray-800 rounded w-full"
                    />
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSaveChatName(chat.id);
                      }}
                      className="ml-2 px-2 py-1 bg-green-500 text-white rounded hover:bg-green-600"
                    >
                      Save
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCancelEdit();
                      }}
                      className="ml-2 px-2 py-1 bg-gray-500 text-white rounded hover:bg-gray-600"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  // Display chat name with edit and delete icons
                  <>
                    <div>
                      {chat.name} - {chat.date}
                    </div>
                    <div className="flex space-x-2">
                      <FaEdit
                        className="cursor-pointer text-gray-600 dark:text-gray-300"
                        onClick={(e) => {
                          e.stopPropagation();
                          startEditingChat(chat.id, chat.name);
                        }}
                      />
                      <FaTrash
                        className="cursor-pointer text-red-500"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteChat(chat.id);
                        }}
                      />
                    </div>
                  </>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
};

export default Sidebar;
