import React, { useState, useEffect, ChangeEvent, KeyboardEvent } from "react"
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib"

interface Args {
  correctAnswer: string
}

function CustomInput(props: { args: Args }) {
  const { correctAnswer } = props.args
  const [val, setVal] = useState<string>("")

  // Whenever the problem changes, clear any residual input
  useEffect(() => {
    setVal("")
  }, [correctAnswer])

  // 1) onChange updates local state
  const onChange = (e: ChangeEvent<HTMLInputElement>) => {
    setVal(e.target.value)
  }

  // 2) onKeyDown watches for the final keystroke, ignoring repeats
  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.repeat) {
      return
    }

    // Compute the next value after this key
    const next = e.key.length === 1 ? val + e.key : val

    // If it matches exactly, submit and clear
    if (next === correctAnswer) {
      Streamlit.setComponentValue(next)
      setVal("")
    }
  }

  // 3) Keep iframe height updated
  useEffect(() => {
    Streamlit.setFrameHeight()
  }, [val])

  return (
    <input
      value={val}
      onChange={onChange}
      onKeyDown={onKeyDown}
      style={{ fontSize: "2rem", padding: "0.5rem", width: "6rem" }}
      autoFocus
    />
  )
}

export default withStreamlitConnection(CustomInput as any)
