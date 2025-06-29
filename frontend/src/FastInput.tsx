import React, { useState, useEffect } from "react"
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib"

interface Props {
  /** Always receive the “controlled” value from Python */
  value?: string
}

function FastInput({ value = "" }: Props) {
  // (A) Local state
  const [internalValue, setInternalValue] = useState(value)

  // (B) On *every* prop change, override local state
  useEffect(() => {
    console.log("[FastInput] Prop changed →", JSON.stringify(value))
    setInternalValue(value)
  }, [value])

  // (C) On keystroke, update local state AND notify Streamlit
  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value
    setInternalValue(v)
    Streamlit.setComponentValue(v)
  }

  // (D) Auto-resize iframe
  useEffect(() => {
    Streamlit.setFrameHeight()
  }, [internalValue])

  return (
    <input
      value={internalValue}
      onChange={onChange}
      style={{ fontSize: "2rem", padding: "0.5rem", width: "6rem" }}
      autoFocus
    />
  )
}

export default withStreamlitConnection(FastInput as any)
