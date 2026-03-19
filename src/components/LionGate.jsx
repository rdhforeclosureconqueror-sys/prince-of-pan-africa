import React, { useEffect } from "react";

export default function LionGate({ children, onAuth }) {
  useEffect(() => {
    if (onAuth) {
      onAuth({
        email: "rdhforeclosureconqueror@gmail.com",
        role: "admin",
      });
    }
  }, [onAuth]);

  return <>{children}</>;
}
