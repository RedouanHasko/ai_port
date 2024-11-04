import React, { useEffect, useState } from "react";

interface ToastProps {
  message: string;
  type?: "success" | "error";
  onClose: () => void;
  duration?: number; // Duration in milliseconds
}

const Toast: React.FC<ToastProps> = ({
  message,
  type = "success",
  onClose,
  duration = 3000,
}) => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => prev + 100 / (duration / 50));
    }, 50);

    const timer = setTimeout(() => {
      clearInterval(interval);
      onClose();
    }, duration);

    return () => {
      clearTimeout(timer);
      clearInterval(interval);
    };
  }, [duration, onClose]);

  return (
    <div
      className={`fixed bottom-4 left-1/2 transform -translate-x-1/2 p-4 rounded-lg shadow-lg text-white overflow-hidden ${
        type === "success" ? "bg-green-500" : "bg-red-500"
      }`}
      style={{ width: "90%", maxWidth: "300px" }} // Responsive width
    >
      <div>{message}</div>
      <div
        className="h-1 mt-2 rounded bg-white"
        style={{
          width: `${progress}%`,
          transition: "width 50ms linear",
        }}
      />
    </div>
  );
};

export default Toast;
