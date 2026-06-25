import React from "react";
import {
  activationRequirements,
  formatMutualAidCurrency,
  getMutualAidFundProgress,
} from "../mutualAidFundProgress";

export default function MutualAidFundProgressCard() {
  const progress = getMutualAidFundProgress();

  return (
    <article className="mutual-aid-card mutual-aid-fund-progress" aria-labelledby="mutual-aid-fund-progress-title">
      <div className="mutual-aid-card__header">
        <h2 id="mutual-aid-fund-progress-title">Mutual Aid Fund Progress</h2>
        <span className="mutual-aid-status mutual-aid-status--compact">{progress.status}</span>
      </div>

      <div className="mutual-aid-progress" aria-label={`Fund progress is ${progress.percentage}% toward activation`}>
        <div className="mutual-aid-progress__bar" style={{ width: `${progress.percentage}%` }} />
      </div>

      <dl className="mutual-aid-progress-stats">
        <div>
          <dt>Activation threshold</dt>
          <dd>{formatMutualAidCurrency(progress.threshold)}</dd>
        </div>
        <div>
          <dt>Current progress</dt>
          <dd>{formatMutualAidCurrency(progress.current)}</dd>
        </div>
        <div>
          <dt>Remaining amount to activation</dt>
          <dd>{formatMutualAidCurrency(progress.remaining)}</dd>
        </div>
      </dl>

      <p className="mutual-aid-note">
        This is a read-only planning display value only. It does not track live giving, process payments, create records,
        or represent a member-specific fund amount.
      </p>
      <p className="mutual-aid-note">
        No distributions before activation. Support is not promised or assured, and fund progress is not a
        member-specific balance.
      </p>
      <div className="mutual-aid-requirements-note">
        <p>Activation also requires:</p>
        <ul className="mutual-aid-list">
          {activationRequirements.map((requirement) => (
            <li key={requirement}>{requirement}</li>
          ))}
        </ul>
      </div>
    </article>
  );
}
