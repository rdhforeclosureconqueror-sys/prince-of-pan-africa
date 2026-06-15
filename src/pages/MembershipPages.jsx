import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { post } from "../api/api";
import "../styles/membership.css";

const foundationalTexts = [
  "Blackonomics",
  "B.I.B.L.E.",
  "Forgotten Black Mega Cities",
  "Rite of Passage materials",
  "Future foundational publications",
];

const ecosystemPillars = [
  "Education",
  "Economic cooperation",
  "Health and wellness",
  "Publishing and storytelling",
  "Leadership development",
  "Cultural preservation",
  "Local business networks",
  "Mutual aid",
  "Community ownership",
  "Institution building",
];

const communityBenefits = [
  "Access to community resources",
  "Access to library and educational materials",
  "Participation in community discussions",
  "Member orientation materials",
  "Community updates",
  "Access to foundational learning paths",
  "Entry into the Simba wa Ujamaa ecosystem",
  "Support for the long-term mission",
];

const builderBenefits = [
  "Everything in Community Membership",
  "Early access to ecosystem projects",
  "Testing opportunities",
  "Community development participation",
  "Feedback participation",
  "Outreach participation",
  "Builder-focused discussions and channels",
  "Deeper involvement in shaping the ecosystem",
  "Updates on future tools, services, and community initiatives",
];

const builderParticipation = [
  "Reviewing educational materials",
  "Testing onboarding flows",
  "Giving feedback on membership structure",
  "Helping refine Discord/community organization",
  "Participating in project discussions",
  "Sharing community needs and ideas",
  "Supporting outreach",
  "Helping identify future opportunities",
];

function MembershipHero({ kicker, title, subtitle, children }) {
  return (
    <section className="membership-hero cosmic-readable-shell">
      <p className="membership-kicker">{kicker}</p>
      <h1>{title}</h1>
      <p className="membership-subtitle">{subtitle}</p>
      {children}
    </section>
  );
}

function MembershipCtaRow() {
  return (
    <div className="membership-cta-row">
      <Link to="/membership/community" className="membership-btn membership-btn--gold">
        Become a Community Member
      </Link>
      <Link to="/membership/builder" className="membership-btn membership-btn--green">
        Become a Builder Member
      </Link>
      <a href="#mission" className="membership-btn membership-btn--ghost">
        Explore the Mission
      </a>
    </div>
  );
}

function CheckoutButton({ plan, children, className }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function startCheckout() {
    setError("");
    setLoading(true);
    try {
      const response = await post("/billing/checkout", { plan });
      if (response?.checkout_url) {
        window.location.assign(response.checkout_url);
        return;
      }
      throw new Error("Checkout URL was not returned.");
    } catch (err) {
      if (err.status === 401) {
        navigate("/?auth=join");
        return;
      }
      setError(err.message || "Unable to start checkout.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <button type="button" className={className} onClick={startCheckout} disabled={loading}>
        {loading ? "Opening Stripe…" : children}
      </button>
      {error && <p className="membership-error" role="alert">{error}</p>}
    </div>
  );
}

function PlanCard({ plan, price, statement, description, benefits, to, variant }) {
  return (
    <article className={`membership-plan membership-plan--${variant}`}>
      <p className="membership-plan__eyebrow">{plan}</p>
      <h2>{price}</h2>
      <p className="membership-plan__statement">“{statement}”</p>
      <p>{description}</p>
      <ul>
        {benefits.map((benefit) => (
          <li key={benefit}>{benefit}</li>
        ))}
      </ul>
      <Link to={to} className="membership-btn membership-btn--wide">
        Learn About {plan}
      </Link>
    </article>
  );
}

export function MembershipOverviewPage() {
  return (
    <main className="membership-shell">
      <MembershipHero
        kicker="Simba wa Ujamaa Membership"
        title="Rebuilding Community Capacity for the Future"
        subtitle="Simba wa Ujamaa is a community-supported ecosystem for education, economic cooperation, health, publishing, leadership development, and institution building."
      >
        <p className="membership-hero-question">What are we building together?</p>
        <p>
          We are building a modern community hub that helps people learn, organize, create, publish, heal, lead,
          and support one another through shared systems.
        </p>
        <MembershipCtaRow />
      </MembershipHero>

      <section id="mission" className="membership-section cosmic-readable-shell">
        <p className="membership-kicker">The Mission</p>
        <h2>A Community-Building Mission</h2>
        <p>
          Membership is not simply about unlocking content. Membership is a way to support and participate in the
          mission of rebuilding community capacity.
        </p>
        <div className="membership-chip-grid">
          {ecosystemPillars.map((pillar) => (
            <span key={pillar}>{pillar}</span>
          ))}
        </div>
      </section>

      <section className="membership-section cosmic-readable-shell">
        <p className="membership-kicker">Membership Paths</p>
        <h2>Choose How You Support the Mission</h2>
        <div className="membership-plan-grid">
          <PlanCard
            plan="Community Member"
            price="$10/month"
            statement="I support the mission."
            description="Community Members help sustain the foundation of Simba wa Ujamaa through educational resources, discussion spaces, library access, and ecosystem growth."
            benefits={communityBenefits.slice(0, 6)}
            to="/membership/community"
            variant="community"
          />
          <PlanCard
            plan="Builder Member"
            price="$25.99/month"
            statement="I help build the mission."
            description="Builder Members support the mission at a deeper participation level by helping test, shape, improve, and expand the ecosystem."
            benefits={builderBenefits.slice(0, 7)}
            to="/membership/builder"
            variant="builder"
          />
        </div>
      </section>

      <section className="membership-section cosmic-readable-shell">
        <p className="membership-kicker">Foundational Texts</p>
        <h2>Start With the Foundation</h2>
        <p>
          The books and educational materials are not side resources. They help explain the purpose, history, and
          principles that guide the ecosystem.
        </p>
        <ul className="membership-list membership-list--columns">
          {foundationalTexts.map((text) => (
            <li key={text}>{text}</li>
          ))}
        </ul>
        <Link to="/library" className="membership-btn membership-btn--gold">
          Explore the Foundational Texts
        </Link>
      </section>
    </main>
  );
}

export function CommunityMembershipPage() {
  return (
    <main className="membership-shell">
      <MembershipHero
        kicker="Community Member"
        title="“I support the mission.”"
        subtitle="Community Membership is for people who believe in the mission of Simba wa Ujamaa and want to help sustain the ecosystem."
      >
        <div className="membership-price-card">
          <strong>$10/month</strong>
          <span>Support the mission and join the Simba wa Ujamaa ecosystem.</span>
        </div>
      </MembershipHero>

      <section className="membership-section cosmic-readable-shell">
        <h2>Why Community Membership Exists</h2>
        <p>
          Simba wa Ujamaa is being built to support long-term community development. Community Membership helps
          provide the foundation for educational materials, community spaces, publishing tools, health and wellness
          systems, leadership development resources, economic cooperation tools, and technology that supports
          community ownership and participation.
        </p>
      </section>

      <section className="membership-section cosmic-readable-shell">
        <h2>What Community Members Receive</h2>
        <ul className="membership-list membership-list--columns">
          {communityBenefits.map((benefit) => (
            <li key={benefit}>{benefit}</li>
          ))}
        </ul>
      </section>

      <section className="membership-section cosmic-readable-shell">
        <h2>Foundational Study</h2>
        <p>
          Community Members are encouraged to begin with the foundational texts of the ecosystem. These works help
          explain why Simba wa Ujamaa exists and how education, economics, leadership, culture, and responsibility
          connect to institution building.
        </p>
        <ul className="membership-list membership-list--columns">
          {foundationalTexts.map((text) => (
            <li key={text}>{text}</li>
          ))}
        </ul>
      </section>

      <section className="membership-section membership-final-cta cosmic-readable-shell">
        <h2>Become a Community Member</h2>
        <p>Support the mission for $10/month and help sustain the foundation of Simba wa Ujamaa.</p>
        <div className="membership-cta-row">
          <CheckoutButton plan="community" className="membership-btn membership-btn--gold">
            Join as a Community Member
          </CheckoutButton>
          <Link to="/membership/builder" className="membership-btn membership-btn--ghost">
            Learn About Builder Membership
          </Link>
        </div>
      </section>
    </main>
  );
}

export function BuilderMembershipPage() {
  return (
    <main className="membership-shell">
      <MembershipHero
        kicker="Builder Member"
        title="“I help build the mission.”"
        subtitle="Builder Membership is for those who want to participate more deeply in the development of Simba wa Ujamaa."
      >
        <div className="membership-price-card membership-price-card--builder">
          <strong>$25.99/month</strong>
          <span>Support the mission while helping shape the ecosystem through feedback, testing, outreach, and community development discussions.</span>
        </div>
      </MembershipHero>

      <section className="membership-section cosmic-readable-shell">
        <h2>The Builder Role</h2>
        <p>
          Builder Members help move the mission from concept to infrastructure. This is not simply a higher content
          tier. Builder Membership is a participation role for people asking, “What are we building, and how can I
          help?”
        </p>
      </section>

      <section className="membership-section cosmic-readable-shell">
        <h2>What Builder Members Receive</h2>
        <ul className="membership-list membership-list--columns">
          {builderBenefits.map((benefit) => (
            <li key={benefit}>{benefit}</li>
          ))}
        </ul>
      </section>

      <section className="membership-section cosmic-readable-shell">
        <h2>Builder Participation May Include</h2>
        <ul className="membership-list membership-list--columns">
          {builderParticipation.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="membership-section membership-final-cta cosmic-readable-shell">
        <h2>Become a Builder Member</h2>
        <p>Support and help build the Simba wa Ujamaa ecosystem for $25.99/month.</p>
        <div className="membership-cta-row">
          <CheckoutButton plan="builder" className="membership-btn membership-btn--green">
            Join as a Builder Member
          </CheckoutButton>
          <Link to="/membership/community" className="membership-btn membership-btn--ghost">
            Compare Community Membership
          </Link>
        </div>
      </section>
    </main>
  );
}
