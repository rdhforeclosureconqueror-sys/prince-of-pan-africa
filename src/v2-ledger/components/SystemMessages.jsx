import React, { useEffect, useState } from 'react';

const messages = [
  '3 Shares = 1 STAR',
  'Stars convert to Black Dollars',
  'Community participation builds trust equity',
  'Approved reviews earn STAR rewards',
];

export default function SystemMessages() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setIndex(i => (i + 1) % messages.length), 5000);
    return () => clearInterval(timer);
  }, []);

  return <div className="system-messages">{messages[index]}</div>;
}
