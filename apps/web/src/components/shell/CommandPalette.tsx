"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from "@/components/ui/command";
import { navItems } from "@/lib/navigation";
import { Moon, Sun, ArrowRight, Settings2 } from "lucide-react";
import { useTheme } from "next-themes";

export function CommandPalette({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const router = useRouter();
  const { theme, setTheme } = useTheme();

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Navigate, run actions, inspect telemetry…" />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>

        <CommandGroup heading="Navigate">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <CommandItem
                key={item.key}
                value={`${item.label} ${item.section}`}
                onSelect={() => {
                  onOpenChange(false);
                  router.push(item.href);
                }}
              >
                <Icon className="mr-2 h-4 w-4 opacity-80" />
                <span className="flex-1">{item.label}</span>
                <ArrowRight className="h-3.5 w-3.5 opacity-50" />
              </CommandItem>
            );
          })}
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Actions">
          <CommandItem
            value="Toggle theme"
            onSelect={() => {
              setTheme(theme === "dark" ? "light" : "dark");
              onOpenChange(false);
            }}
          >
            {theme === "dark" ? (
              <Sun className="mr-2 h-4 w-4 opacity-80" />
            ) : (
              <Moon className="mr-2 h-4 w-4 opacity-80" />
            )}
            <span className="flex-1">Toggle theme</span>
            <CommandShortcut>⇧T</CommandShortcut>
          </CommandItem>

          <CommandItem
            value="Open settings"
            onSelect={() => {
              onOpenChange(false);
              router.push("/settings");
            }}
          >
            <Settings2 className="mr-2 h-4 w-4 opacity-80" />
            <span className="flex-1">Settings</span>
            <CommandShortcut>G S</CommandShortcut>
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}

