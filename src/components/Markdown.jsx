import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// AI 的回答是 Markdown（程式碼區塊、表格、清單），用這個元件顯示
export default function Markdown({ children }) {
  return (
    <div className="markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{ a: (props) => <a {...props} target="_blank" rel="noreferrer" /> }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
