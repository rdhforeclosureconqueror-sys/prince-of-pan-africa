import React from "react";
import { LEADERSHIP_OPTIONS } from "../../data/leadershipQuestions";

export default function QuestionBlock({ index, prompt, value, onChange }) {
  return (
    <div className="leadership-question">
      <p className="leadership-question__title">
        <span>Q{index + 1}.</span> {prompt}
      </p>
      <div className="leadership-question__options">
        {LEADERSHIP_OPTIONS.map((option) => (
          <label key={option.value}>
            <input
              type="radio"
              name={`question-${index}`}
              value={option.value}
              checked={value === option.value}
              onChange={(event) => onChange(index, event.target.value)}
              required
            />
            {option.label}
          </label>
        ))}
      </div>
    </div>
  );
}
