import React from "react";
import { Link, useParams } from "react-router-dom";
import { findFirst100FullChapter } from "../data/first100DaysFullChapters";
import "../styles/societyBuilder.css";

export default function First100DaysChapterReaderPage() {
  const { societyId, chapterId } = useParams();
  const chapter = findFirst100FullChapter(chapterId);

  return <main className="society-builder-shell trust-command-shell first100-reader-shell">
    <div className="society-actions">
      <Link className="society-btn secondary" to={`/societies/${societyId}/trust-board`}>Back to Trust Board</Link>
    </div>
    {!chapter ? <section className="society-card first100-reader-card">
      <p className="society-kicker">Full Chapter Reader</p>
      <h1>Full chapter text has not been connected yet.</h1>
      <p className="society-muted">The Container Guide still works on the Trust Board. Use Open Guide for the operational breakdown while the full handbook text is connected.</p>
    </section> : <article className="society-card first100-reader-card">
      <p className="society-kicker">Full Chapter Reader</p>
      <h1>{chapter.chapter_label}: {chapter.chapter_title}</h1>
      <p className="trust-lede">Complete handbook chapter view for study before turning the lesson into Trust Board work.</p>
      <p className="society-muted">Source: {chapter.source_reference}</p>
      <div className="first100-reader-sections">
        {chapter.full_text_sections.map((section) => <section key={section.heading} className="first100-reader-section">
          <h2>{section.heading}</h2>
          {section.body?.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
          {section.list?.length ? <ul>{section.list.map((item) => <li key={item}>{item}</li>)}</ul> : null}
        </section>)}
      </div>
      {chapter.worksheets_or_tables?.length ? <div className="first100-reader-worksheets">
        {chapter.worksheets_or_tables.map((table) => <section key={table.title} className="first100-reader-section">
          <h2>{table.title}</h2>
          <ul>{table.rows.map((row) => <li key={row}>{row}</li>)}</ul>
        </section>)}
      </div> : null}
    </article>}
  </main>;
}
