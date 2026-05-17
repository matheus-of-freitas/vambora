"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { Input } from "@/shared/components/ui/input";

const sanitize = (raw: string): string => raw.trim().toUpperCase();

export const LineSearch = () => {
  const router = useRouter();
  const [value, setValue] = useState("");

  const onSubmit = (e: FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    const cleaned = sanitize(value);
    if (!cleaned) return;
    router.push(`/lines/${encodeURIComponent(cleaned)}`);
  };

  return (
    <form onSubmit={onSubmit} aria-label="Buscar linha">
      <Input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Linha (ex: 485)"
        aria-label="Número ou código da linha"
        className="h-8 w-32"
        autoComplete="off"
        spellCheck={false}
      />
    </form>
  );
};
