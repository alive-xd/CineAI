"use client";

import { ReactNode, useEffect } from "react";
import { SWRConfig } from "swr";

import { useAuthStore } from "@/store/authStore";

type Props = {
  children: ReactNode;
};

export default function Providers({
  children,
}: Props) {

  useEffect(() => {

    useAuthStore
      .getState()
      .loadUser();

    const handleLogout = () => {
      useAuthStore
        .getState()
        .logout();
    };

    window.addEventListener(
      "auth:logout",
      handleLogout
    );

    return () => {
      window.removeEventListener(
        "auth:logout",
        handleLogout
      );
    };

  }, []);

  return (
    <SWRConfig
      value={{
        revalidateOnFocus: false,
        shouldRetryOnError: false,
      }}
    >
      {children}
    </SWRConfig>
  );
}