import React, { useState, useEffect, ChangeEvent, KeyboardEvent } from "react"
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib"

interface Args {
  correctAnswer: string
  alignment: string
  problemId: number
}

function CustomInput(props: { args: Args }) {
  const { correctAnswer = "", alignment = "center", problemId} = props.args
  const [val, setVal] = useState<string>("")
  const [keystrokeHistory, setKeystrokeHistory] = useState<Array<{key: string, timestamp: number}>>([])
  const [keystrokeCount, setKeystrokeCount] = useState(0)

  // Whenever the problem changes, clear any residual input
  useEffect(() => {
    console.log("The problem was answered correctly, clearing input...")
    setVal("")
    setKeystrokeHistory([])
  }, [correctAnswer, problemId])

  // 1) onChange updates local state
  const onChange = (e: ChangeEvent<HTMLInputElement>) => {
    setVal(e.target.value)
  }

  // 2) onKeyDown watches for the final keystroke, ignoring repeats
  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    const updatedKeystrokeCount = keystrokeCount + 1
    const newKeystroke = {key: e.key, timestamp: Date.now()}
    const updatedKeystrokeHistory = keystrokeHistory.concat(newKeystroke)
    setKeystrokeCount(updatedKeystrokeCount)
    setKeystrokeHistory(updatedKeystrokeHistory)

    if (e.repeat) {
      return
    }

    // Compute the next value after this key
    const next = e.key.length === 1 ? val + e.key : val

    // If it matches exactly, submit and clear
    if (next === correctAnswer) {
      e.preventDefault()
      Streamlit.setComponentValue([next, problemId, updatedKeystrokeHistory, updatedKeystrokeCount])
      setVal("")
      setKeystrokeHistory([])
      setKeystrokeCount(0)
    }
  }
  const font_size = "3rem"
  const box_height = "4rem"
  const box_width =  "12rem"
  // 3) Keep iframe height updated
  useEffect(() => {
    Streamlit.setFrameHeight((parseInt(box_height.slice(0,-3), 10))*16*2)
  }, [val])

  return (
  <div style={{
    display: 'flex',
    justifyContent: alignment,
    alignItems: alignment,
    height: '100%',
    width: '100%'
  }}>
    <input
      value={val}
      onChange={onChange}
      onKeyDown={onKeyDown}
      maxLength={6}
      style={{
        fontSize: font_size,
        color:"white",
        height: box_height,
        width: box_width,
        textAlign: "center",
        outline: "none",
        backgroundColor: "transparent"
      }}
      autoFocus
    />
  </div>
)
}

export default withStreamlitConnection(CustomInput as any)
