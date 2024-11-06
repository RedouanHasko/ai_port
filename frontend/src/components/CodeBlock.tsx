import React, { useEffect } from "react";
import Prism from "prismjs";
import "prismjs/themes/prism-coy.css";
import "prismjs/components/prism-python";
import "prismjs/components/prism-javascript";

interface CodeBlockProps {
  language: string;
  content: string;
}

const CodeBlock: React.FC<CodeBlockProps> = ({ language, content }) => {
  useEffect(() => {
    Prism.highlightAll();
  }, [content]);

  return (
    <pre className={`language-${language}`}>
      <code className={`language-${language}`}>{content}</code>
    </pre>
  );
};

export default CodeBlock;
