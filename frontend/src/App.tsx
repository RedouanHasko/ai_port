import React, { useEffect, useState } from "react";
import { ThemeProvider } from "./contexts/ThemeProvider";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import Chat from "./components/Chat";
import Modal from "./components/Modal";
import Toast from "./components/Toast";

interface ChatType {
  id: number;
  name: string;
  date: string;
  messages: { text: string; isUser: boolean }[];
}

const App = () => {
  const [chats, setChats] = useState<ChatType[]>(() =>
    JSON.parse(localStorage.getItem("chats") || "[]")
  );
  const [selectedChat, setSelectedChat] = useState<number | null>(null);
  const [messages, setMessages] = useState<{ text: string; isUser: boolean }[]>(
    []
  );
  const [isSidebarOpen, setSidebarOpen] = useState(true);
  const [models, setModels] = useState<string[]>([]);
  const [selectedLLM, setSelectedLLM] = useState<string>("");

  const [isModalOpen, setModalOpen] = useState(false);
  const [isToastVisible, setToastVisible] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  const [chatToDelete, setChatToDelete] = useState<number | null>(null);

  useEffect(() => {
    localStorage.setItem("chats", JSON.stringify(chats));
  }, [chats]);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/models");
        if (!response.ok) {
          throw new Error("Failed to fetch models");
        }
        const data = await response.json();
        setModels(data.models);
        if (data.models.length > 0) {
          setSelectedLLM(data.models[0]);
        }
      } catch (error) {
        console.error("Error fetching models:", error);
      }
    };
    fetchModels();
  }, []);

  const handleSelectChat = (chatId: number) => {
    const chat = chats.find((c) => c.id === chatId);
    if (chat) {
      setSelectedChat(chatId);
      setMessages(chat.messages);
    }
  };

  const handleAddChat = () => {
    const newChat = {
      id: Date.now(),
      name: `Chat ${chats.length + 1}`,
      date: new Date().toLocaleDateString(),
      messages: [],
    };
    setChats([...chats, newChat]);
    setSelectedChat(newChat.id);
    setMessages([]);
  };

  const handleRenameChat = (chatId: number, newName: string) => {
    setChats((prevChats) =>
      prevChats.map((chat) =>
        chat.id === chatId ? { ...chat, name: newName } : chat
      )
    );
    setToastMessage("Chat renamed successfully!");
    setToastVisible(true);
  };

  const handleDeleteChat = (chatId: number) => {
    setModalOpen(true);
    setChatToDelete(chatId);
  };

  const confirmDeleteChat = () => {
    if (chatToDelete !== null) {
      setChats(chats.filter((chat) => chat.id !== chatToDelete));
      setSelectedChat(null);
      setMessages([]);
      setChatToDelete(null);
      setModalOpen(false);
      setToastMessage("Chat deleted successfully!");
      setToastVisible(true);
    }
  };

  const closeModal = () => {
    setModalOpen(false);
    setChatToDelete(null);
  };

  const handleSendMessage = async (
    message: string,
    updatedMessages?: any[]
  ) => {
    if (selectedChat !== null && selectedLLM) {
      let updatedChatMessages = updatedMessages;
      if (!updatedMessages) {
        updatedChatMessages = [...messages, { text: message, isUser: true }];
        setMessages(updatedChatMessages);

        setChats((prevChats) =>
          prevChats.map((chat) =>
            chat.id === selectedChat
              ? {
                  ...chat,
                  messages: updatedChatMessages,
                }
              : chat
          )
        );
      }

      const llmResponseIndex = updatedChatMessages.length;
      setMessages((prev) => [
        ...updatedChatMessages,
        { text: "", isUser: false },
      ]);

      try {
        const response = await fetch("http://127.0.0.1:8000/send-message", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            content: message,
            model: selectedLLM,
            history: updatedChatMessages,
            chat_id: selectedChat,
          }),
        });

        if (!response.ok || !response.body) {
          console.error("Failed to send message:", response.statusText);
          return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let llmResponseText = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          llmResponseText += chunk;

          setMessages((prevMessages) => {
            const newMessages = [...prevMessages];
            newMessages[llmResponseIndex] = {
              text: llmResponseText,
              isUser: false,
            };
            return newMessages;
          });
        }

        setChats((prevChats) =>
          prevChats.map((chat) =>
            chat.id === selectedChat
              ? {
                  ...chat,
                  messages: [
                    ...updatedChatMessages,
                    { text: llmResponseText, isUser: false },
                  ],
                }
              : chat
          )
        );
      } catch (error) {
        console.error("Error:", error);
      }
    }
  };

  const updateMessage = (index: number, newText: string) => {
    if (selectedChat !== null) {
      const updatedMessages = messages.map((msg, i) =>
        i === index ? { ...msg, text: newText } : msg
      );

      const truncatedMessages = updatedMessages.slice(0, index + 1);

      setMessages(truncatedMessages);

      setChats((prevChats) =>
        prevChats.map((chat) =>
          chat.id === selectedChat
            ? {
                ...chat,
                messages: truncatedMessages,
              }
            : chat
        )
      );

      const lastUserMessage = truncatedMessages[index].text;
      handleSendMessage(lastUserMessage, truncatedMessages);
    }
  };

  const handleLLMChange = (llm: string) => {
    setSelectedLLM(llm);
  };

  return (
    <ThemeProvider>
      <div className="flex h-screen overflow-hidden">
        <Sidebar
          chats={chats}
          onSelectChat={handleSelectChat}
          onDeleteChat={handleDeleteChat}
          onAddChat={handleAddChat}
          onRenameChat={handleRenameChat}
          isOpen={isSidebarOpen}
          selectedChatId={selectedChat}
          onCloseSidebar={() => setSidebarOpen(false)}
        />
        <div
          className={`flex flex-col flex-1 bg-gray-100 dark:bg-gray-900 transition-all duration-300 ${
            isSidebarOpen ? "ml-64" : "ml-0"
          }`}
        >
          <Header toggleSidebar={() => setSidebarOpen((open) => !open)} />
          <div className="flex flex-col flex-1 overflow-hidden">
            {models.length > 0 ? (
              <>
                <div className="p-4">
                  <label
                    htmlFor="llm"
                    className="text-gray-700 dark:text-white mr-2"
                  >
                    Choose LLM:
                  </label>
                  <select
                    id="llm"
                    value={selectedLLM}
                    onChange={(e) => handleLLMChange(e.target.value)}
                    className="p-2 border rounded-md border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
                  >
                    {models.map((model) => (
                      <option key={model} value={model}>
                        {model}
                      </option>
                    ))}
                  </select>
                </div>
                <Chat
                  selectedChat={selectedChat}
                  messages={messages}
                  sendMessage={handleSendMessage}
                  updateMessage={updateMessage}
                />
              </>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                No LLM models available. Please ensure Ollama is running and
                models are installed.
              </div>
            )}
          </div>
        </div>

        <Modal
          isOpen={isModalOpen}
          title="Delete Chat"
          message="Are you sure you want to delete this chat?"
          onConfirm={confirmDeleteChat}
          onCancel={closeModal}
        />

        {isToastVisible && (
          <Toast
            message={toastMessage}
            type="success"
            onClose={() => setToastVisible(false)}
          />
        )}
      </div>
    </ThemeProvider>
  );
};

export default App;
