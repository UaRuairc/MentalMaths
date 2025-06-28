import React from "react";
import { createRoot } from "react-dom/client";
import FastInput from "./FastInput";

const container = document.getElementById("root")!;
const root = createRoot(container);
root.render(<FastInput {...(window as any).streamlitComponentProps} />);
