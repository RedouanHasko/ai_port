import React, { useState, useEffect, useRef } from "react";
import { FaEdit } from "react-icons/fa";

interface ChatProps {
  selectedChat: number | null;
  messages: { text: string; isUser: boolean }[];
  sendMessage: (message: string) => void;
  updateMessage: (index: number, newText: string) => void;
}

const Chat: React.FC<ChatProps> = ({
  selectedChat,
  messages,
  sendMessage,
  updateMessage,
}) => {
  const [input, setInput] = useState("");
  const [editingMessageIndex, setEditingMessageIndex] = useState<number | null>(
    null
  );
  const [editedMessage, setEditedMessage] = useState("");
  const [isSending, setIsSending] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Scroll to the bottom whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (input.trim() && !isSending) {
      setIsSending(true);
      sendMessage(input);
      setInput("");
      setIsSending(false);
    }
  };

  const startEditing = (index: number, currentText: string) => {
    setEditingMessageIndex(index);
    setEditedMessage(currentText);
  };

  const saveEditedMessage = () => {
    if (editedMessage.trim() && editingMessageIndex !== null) {
      updateMessage(editingMessageIndex, editedMessage);
      setEditingMessageIndex(null);
      setEditedMessage("");
    }
  };

  const cancelEditing = () => {
    setEditingMessageIndex(null);
    setEditedMessage("");
  };

  if (selectedChat === null) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
        Start a new chat or open a previous one to continue chatting.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat Messages Area */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex ${
              msg.isUser ? "justify-end" : "justify-start"
            } mb-2`}
          >
            <div className="relative group max-w-[70%]">
              {msg.isUser && (
                <FaEdit
                  className="absolute -left-6 top-1/2 transform -translate-y-1/2 text-gray-400 cursor-pointer opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={() => startEditing(index, msg.text)}
                />
              )}
              <div
                className={`p-3 rounded-lg ${
                  msg.isUser
                    ? "bg-blue-500 text-white text-right"
                    : "bg-gray-300 dark:bg-gray-700 text-left"
                }`}
              >
                {editingMessageIndex === index && msg.isUser ? (
                  <div className="flex flex-col">
                    <input
                      type="text"
                      value={editedMessage}
                      onChange={(e) => setEditedMessage(e.target.value)}
                      className="p-2 bg-gray-200 dark:bg-gray-800 rounded-md text-black dark:text-white w-full mb-2"
                    />
                    <div className="flex justify-end space-x-2">
                      <button
                        onClick={saveEditedMessage}
                        className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                      >
                        Save
                      </button>
                      <button
                        onClick={cancelEditing}
                        className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div>{msg.text}</div>
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-gray-100 dark:bg-gray-900 border-t border-gray-300 dark:border-gray-700 sticky bottom-0">
        <div className="flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Type a message..."
            className="flex-1 p-2 border rounded-l-md border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
          />
          <button
            onClick={handleSend}
            className="px-4 py-2 bg-blue-500 text-white rounded-r-md hover:bg-blue-600"
            disabled={isSending}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chat;