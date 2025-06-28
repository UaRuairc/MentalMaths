// frontend/src/FastInput.tsx

import React, { useState, useEffect } from "react";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";

interface Props {
  value: string;
}

function FastInput({ value }: Props) {
  // 1) Keep a local copy of the value so we can control it.
  const [internalValue, setInternalValue] = useState(value);

  // 2) Whenever the outer prop changes (e.g. to ""), update our state.
  useEffect(() => {
    setInternalValue(value);
  }, [value]);

  // Send each keystroke back to Streamlit *and* update local state.
  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    setInternalValue(v);
    Streamlit.setComponentValue(v);
  };

  return (
    <input
      value={internalValue}       // ← controlled by our local state
      onChange={onChange}
      style={{ fontSize: "2rem", padding: "0.5rem", width: "6rem" }}
      autoFocus
    />
  );
}

export default withStreamlitConnection(FastInput as any);
