"use client";
import { useEffect } from "react";
import Shepherd from "shepherd.js";
import "shepherd.js/dist/css/shepherd.css";

const TOUR_KEY = "goatflow_tour_done";

export function OnboardingTour() {
  useEffect(() => {
    if (localStorage.getItem(TOUR_KEY)) return;

    const tour = new Shepherd.Tour({
      useModalOverlay: true,
      defaultStepOptions: {
        cancelIcon: { enabled: true },
        classes: "goatflow-tour-step",
        scrollTo: { behavior: "smooth", block: "center" },
      },
    });

    tour.addStep({
      id: "welcome",
      text: "Welcome to GOATflow. This is your pasture. Let's show you around. 🐐",
      buttons: [{ text: "Let's go →", action: tour.next }],
    });

    tour.addStep({
      id: "horns",
      text: "These are your GOAT Horns — permanent rules that tell the AI what matters most to you. Add at least one before your first churn. Example: 'Family always comes first.'",
      attachTo: { element: ".goat-horns-section", on: "right" },
      buttons: [{ text: "Got it →", action: tour.next }],
    });

    tour.addStep({
      id: "track-sieve",
      text: "This is the Track Sieve. Dump your emails, notes, or tasks here. The Churn Engine will organize them into prioritized Tracks. Be specific — the goat can't chew fog.",
      attachTo: { element: ".track-sieve-section", on: "bottom" },
      buttons: [{ text: "Got it →", action: tour.next }],
    });

    tour.addStep({
      id: "morning-stake",
      text: "Every morning, plant a Stake — one commitment for the day. Honor it and earn Hay. This is your daily accountability anchor.",
      buttons: [{ text: "Got it →", action: tour.next }],
    });

    tour.addStep({
      id: "signal-score",
      text: "Your Signal Score grows as you use GOATflow genuinely. The more specific your inputs, the better your outputs. Your data is private — only your score is ever shared.",
      attachTo: { element: ".signal-score-section", on: "right" },
      buttons: [{ text: "Got it →", action: tour.next }],
    });

    tour.addStep({
      id: "leaderboard",
      text: "The Herd Leaderboard tracks your Hay, streaks, and weekly momentum. Compete, climb, and see where you stand.",
      buttons: [{ text: "Start climbing 🐐", action: tour.complete }],
    });

    tour.on("complete", () => localStorage.setItem(TOUR_KEY, "true"));
    tour.on("cancel", () => localStorage.setItem(TOUR_KEY, "true"));

    const t = setTimeout(() => tour.start(), 1500);

    return () => {
      clearTimeout(t);
      if (tour.isActive()) tour.cancel();
    };
  }, []);

  return null;
}
