import React, { useMemo, useState } from "react";
import { LEADERSHIP_QUESTIONS } from "../../data/leadershipQuestions";
import QuestionBlock from "./QuestionBlock";

export default function LeadershipForm({ onSubmit, loading }) {
  const [answers, setAnswers] = useState(Array(LEADERSHIP_QUESTIONS.length).fill(""));
  const answeredCount = useMemo(() => answers.filter(Boolean).length, [answers]);

  function updateAnswer(index, value) {
    setAnswers((prev) => {
      const next = [...prev];
      next[index] = value;
      return next;
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (answeredCount !== LEADERSHIP_QUESTIONS.length) return;
    await onSubmit(answers);
  }

  return (
    <form className="leadership-form" onSubmit={handleSubmit}>
      <div className="leadership-form__progress">
        <strong>{answeredCount}/30 answered</strong>
        <div>
          Complete every question to generate your leadership dashboard.
        </div>
      </div>

      {LEADERSHIP_QUESTIONS.map((prompt, index) => (
        <QuestionBlock
          key={index}
          index={index}
          prompt={prompt}
          value={answers[index]}
          onChange={updateAnswer}
        />
      ))}

      <button className="leadership-submit" type="submit" disabled={loading || answeredCount < 30}>
        {loading ? "Analyzing leadership profile..." : "Submit Assessment"}
      </button>
    </form>
  );
}
