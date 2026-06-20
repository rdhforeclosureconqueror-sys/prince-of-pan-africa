import React, { useMemo, useState } from "react";
import "../styles/communityDirectory.css";

const PROFILE_KEY = "simba_contribution_profile_v1";

export const COMMUNITY_SKILLS = [
  "Business",
  "Teaching",
  "Technology",
  "Writing",
  "Art",
  "Music",
  "Health",
  "Fitness",
  "Construction",
  "Agriculture",
  "Finance",
  "Child Development",
  "History",
  "Language Learning",
  "Community Organizing",
  "Cooking",
  "Gardening",
  "Transportation",
  "Legal",
  "Healthcare",
  "Engineering",
  "Media",
  "Administration",
];

const DEFAULT_PROFILE = {
  firstName: "",
  city: "",
  state: "",
  country: "",
  photoUrl: "",
  businesses: "",
  languagesLearning: "",
  booksCompleted: "",
  assessmentsCompleted: "",
  starRank: "",
  interests: [],
  skills: [],
  visibility: {
    firstName: false,
    location: false,
    photoUrl: false,
    interests: false,
    skills: false,
    businesses: false,
    languagesLearning: false,
    booksCompleted: false,
    assessmentsCompleted: false,
    starRank: false,
  },
};

const DEMO_MEMBERS = [
  {
    id: "sample-atlanta",
    firstName: "Amina",
    city: "Atlanta",
    state: "GA",
    country: "United States",
    interests: ["Business", "Community Organizing", "History"],
    skills: ["Teaching", "Administration"],
    languagesLearning: "Swahili",
    businesses: "Cooperative bookstore",
    starRank: "Builder",
    recentlyActive: true,
  },
  {
    id: "sample-lagos",
    firstName: "Kwame",
    city: "Lagos",
    state: "Lagos",
    country: "Nigeria",
    interests: ["Technology", "Media", "Language Learning"],
    skills: ["Engineering", "Writing"],
    languagesLearning: "Yoruba",
    businesses: "Digital media studio",
    starRank: "Member",
    recentlyActive: true,
  },
  {
    id: "sample-kingston",
    firstName: "Nia",
    city: "Kingston",
    state: "Surrey",
    country: "Jamaica",
    interests: ["Agriculture", "Cooking", "Health"],
    skills: ["Gardening", "Community Organizing"],
    languagesLearning: "Swahili",
    businesses: "Community garden",
    starRank: "Rising STAR",
    recentlyActive: false,
  },
];

function loadProfile() {
  try {
    return { ...DEFAULT_PROFILE, ...JSON.parse(window.localStorage.getItem(PROFILE_KEY) || "{}") };
  } catch {
    return DEFAULT_PROFILE;
  }
}

function hasPublicProfile(profile) {
  return Object.values(profile.visibility || {}).some(Boolean);
}

function toggleListValue(list, value) {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value];
}

function visibleProfile(profile) {
  const display = { id: "you", recentlyActive: true, isYou: true };
  if (profile.visibility.firstName) display.firstName = profile.firstName || "Member";
  if (profile.visibility.location) {
    display.city = profile.city;
    display.state = profile.state;
    display.country = profile.country;
  }
  if (profile.visibility.photoUrl) display.photoUrl = profile.photoUrl;
  if (profile.visibility.interests) display.interests = profile.interests;
  if (profile.visibility.skills) display.skills = profile.skills;
  if (profile.visibility.businesses) display.businesses = profile.businesses;
  if (profile.visibility.languagesLearning) display.languagesLearning = profile.languagesLearning;
  if (profile.visibility.booksCompleted) display.booksCompleted = profile.booksCompleted;
  if (profile.visibility.assessmentsCompleted) display.assessmentsCompleted = profile.assessmentsCompleted;
  if (profile.visibility.starRank) display.starRank = profile.starRank;
  return display;
}

export default function CommunityDirectoryPage() {
  const [profile, setProfile] = useState(loadProfile);
  const [filters, setFilters] = useState({ state: "", city: "", country: "", interest: "", language: "", business: "", skill: "", starRank: "", activeOnly: false });

  const updateProfile = (field, value) => setProfile((current) => ({ ...current, [field]: value }));
  const updateVisibility = (field) => setProfile((current) => ({ ...current, visibility: { ...current.visibility, [field]: !current.visibility[field] } }));
  const saveProfile = () => window.localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));

  const members = useMemo(() => [hasPublicProfile(profile) ? visibleProfile(profile) : null, ...DEMO_MEMBERS].filter(Boolean), [profile]);
  const filteredMembers = members.filter((member) => {
    const memberInterests = [...(member.interests || []), ...(member.skills || [])].join(" ").toLowerCase();
    return (!filters.state || member.state?.toLowerCase().includes(filters.state.toLowerCase()))
      && (!filters.city || member.city?.toLowerCase().includes(filters.city.toLowerCase()))
      && (!filters.country || member.country?.toLowerCase().includes(filters.country.toLowerCase()))
      && (!filters.interest || memberInterests.includes(filters.interest.toLowerCase()))
      && (!filters.skill || (member.skills || []).join(" ").toLowerCase().includes(filters.skill.toLowerCase()))
      && (!filters.language || member.languagesLearning?.toLowerCase().includes(filters.language.toLowerCase()))
      && (!filters.business || member.businesses?.toLowerCase().includes(filters.business.toLowerCase()))
      && (!filters.starRank || member.starRank?.toLowerCase().includes(filters.starRank.toLowerCase()))
      && (!filters.activeOnly || member.recentlyActive);
  });

  return (
    <main className="community-directory admin-dashboard cosmic-readable-shell">
      <header className="dashboard-header community-directory__hero">
        <p className="member-kicker">Community Directory · Contribution Network</p>
        <h1>Find your people. Build together.</h1>
        <p className="subtitle">Members choose what to share. Privacy comes first; belonging comes next.</p>
      </header>

      <section className="community-directory__grid">
        <article className="cosmic-section community-card community-card--wide">
          <div className="section-heading-row"><div><p className="section-kicker">Contribution Profile</p><h2>Create your public presence</h2></div><button className="member-action-btn" type="button" onClick={saveProfile}>Save Profile</button></div>
          <p>Nothing appears in the directory unless you turn on its visibility switch.</p>
          <div className="profile-form-grid">
            {["firstName", "city", "state", "country", "photoUrl", "businesses", "languagesLearning", "booksCompleted", "assessmentsCompleted", "starRank"].map((field) => (
              <label key={field}>{field.replace(/([A-Z])/g, " $1")}<input value={profile[field]} onChange={(event) => updateProfile(field, event.target.value)} /></label>
            ))}
          </div>
          <div className="skill-picker">
            <h3>Self-selected interests and skills</h3>
            {COMMUNITY_SKILLS.map((skill) => (
              <button key={skill} type="button" className={profile.interests.includes(skill) || profile.skills.includes(skill) ? "is-selected" : ""} onClick={() => setProfile((current) => ({ ...current, interests: toggleListValue(current.interests, skill), skills: toggleListValue(current.skills, skill) }))}>{skill}</button>
            ))}
          </div>
          <div className="privacy-grid">
            {Object.keys(profile.visibility).map((field) => <label key={field}><input type="checkbox" checked={profile.visibility[field]} onChange={() => updateVisibility(field)} /> Show {field.replace(/([A-Z])/g, " $1")}</label>)}
          </div>
        </article>

        <article className="cosmic-section community-card">
          <p className="section-kicker">Currently Active In</p><h2>Contribution Summary</h2>
          <ul className="contribution-list"><li>Learning: {profile.interests.length ? profile.interests.join(" · ") : "Not shared yet"}</li><li>Business: {profile.businesses || "Not shared yet"}</li><li>Languages: {profile.languagesLearning || "Not shared yet"}</li><li>Reading: {profile.booksCompleted || "Not shared yet"}</li><li>Community Participation: Directory profile</li><li>Assessments: {profile.assessmentsCompleted || "Not shared yet"}</li></ul>
        </article>

        <article className="cosmic-section community-card community-card--wide">
          <p className="section-kicker">Find Community Members</p><h2>Search the cooperative network</h2>
          <div className="directory-filters">
            {Object.keys(filters).filter((key) => key !== "activeOnly").map((key) => <input key={key} placeholder={key.replace(/([A-Z])/g, " $1")} value={filters[key]} onChange={(event) => setFilters((current) => ({ ...current, [key]: event.target.value }))} />)}
            <label><input type="checkbox" checked={filters.activeOnly} onChange={() => setFilters((current) => ({ ...current, activeOnly: !current.activeOnly }))} /> Recently Active</label>
          </div>
          <div className="member-results">{filteredMembers.map((member) => <article key={member.id} className="member-result-card"><strong>{member.firstName || "Member"}{member.isYou ? " (You)" : ""}</strong><span>{[member.city, member.state, member.country].filter(Boolean).join(", ") || "Location private"}</span><p>{[...(member.interests || []), ...(member.skills || [])].join(" · ") || "Interests private"}</p><small>{member.languagesLearning ? `Learning ${member.languagesLearning}` : "Languages private"} · {member.starRank || "STAR private"}</small></article>)}</div>
        </article>

        <article className="cosmic-section community-card"><p className="section-kicker">Community Projects</p><h2>No projects yet.</h2><p>Future members will be able to join cooperative projects together.</p></article>
        <article className="cosmic-section community-card"><p className="section-kicker">Volunteer Opportunities</p><h2>Coming Soon</h2><p>Teaching · Translation · Library · Book Reviews · Moderation · Events · Technology · Community Outreach</p></article>
        <article className="cosmic-section community-card"><p className="section-kicker">Community Around the World</p><h2>Map Placeholder</h2><p>Eventually members can choose to appear on a world map.</p></article>
        <article className="cosmic-section community-card"><p className="section-kicker">Member Profile Spaces</p><h2>Reserved for growth</h2><p>Journey · Achievements · Reading · Languages · Businesses · Projects · Contributions · STAR · Current Growth Focus · Community Characteristics (Coming Soon) · Community Archetypes (Coming Soon)</p></article>
      </section>
    </main>
  );
}
