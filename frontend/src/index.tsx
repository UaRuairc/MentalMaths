import React from "react";
import { createRoot } from "react-dom/client";
import CustomInput from "./CustomInput";

const container = document.getElementById("root")!;
const root = createRoot(container);
root.render(<CustomInput {...(window as any).streamlitComponentProps} />);
