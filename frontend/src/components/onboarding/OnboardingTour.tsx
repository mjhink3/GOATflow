"use client";
import { useEffect } from "react";
import Shepherd from "shepherd.js";
import "shepherd.js/dist/css/shepherd.css";

const TOUR_KEY = "goatflow_tour_done";

function dispatchTourComplete() {
  window.dispatchEvent(new CustomEvent("goatflow:tour-complete"));
}

export function OnboardingTour() {
  useEffect(() => {
    if (localStorage.getItem(TOUR_KEY)) {
      // Already done — immediately unblock the stake gate
      dispatchTourComplete();
      return;
    }

    const tour = new Shepherd.Tour({
      useModalOverlay: true,
      defaultStepOptions: {
        cancelIcon: { enabled: true },
        classes: "goatflow-tour-step",
        scrollTo: { behavior: "smooth", block: "center" },
        arrow: false,
      },
    });

    tour.addStep({
      id: "welcome",
      arrow: false,
      text: "Welcome to GOATflow. This is your pasture. Let's show you around. 🐐",
      buttons: [{ text: "Let's go →", action: tour.next }],
    });

    tour.addStep({
      id: "horns",
      arrow: false,
      text: "These are your GOAT Horns — permanent rules that tell the AI what matters most to you. Add at least one before your first churn. Example: 'Family always comes first.'",
      attachTo: { element: ".goat-horns-section", on: "right" },
      buttons: [{ text: "Got it →", action: tour.next }],
    });

    tour.addStep({
      id: "track-sieve",
      arrow: false,
      text: "This is the Track Sieve. Dump your emails, notes, or tasks here. The Churn Engine will organize them into prioritized Tracks. Be specific — the goat can't chew fog.",
      attachTo: { element: ".track-sieve-section", on: "bottom" },
      buttons: [{ text: "Got it →", action: tour.next }],
    });

    tour.addStep({
      id: "morning-stake",
      arrow: false,
      text: "Every morning, plant a Stake — one commitment for the day. Honor it and earn Hay. This is your daily accountability anchor.",
      buttons: [{ text: "Got it →", action: tour.next }],
    });

    tour.addStep({
      id: "signal-score",
      arrow: false,
      text: "Your Signal Score grows as you use GOATflow genuinely. The more specific your inputs, the better your outputs. Your data is private — only your score is ever shared.",
      attachTo: { element: ".signal-score-section", on: "right" },
      buttons: [{ text: "Got it →", action: tour.next }],
    });

    tour.addStep({
      id: "leaderboard",
      arrow: false,
      text: "The Herd Leaderboard tracks your Hay, streaks, and weekly momentum. Compete, climb, and see where you stand.",
      buttons: [{ text: "Start climbing 🐐", action: tour.complete }],
    });

    tour.on("complete", () => {
      localStorage.setItem(TOUR_KEY, "true");
      dispatchTourComplete();
    });
    tour.on("cancel", () => {
      localStorage.setItem(TOUR_KEY, "true");
      dispatchTourComplete();
    });

    let fallbackTimer: ReturnType<typeof setTimeout> | null = null;

    function startTour() {
      if (fallbackTimer) clearTimeout(fallbackTimer);
      if (!localStorage.getItem(TOUR_KEY) && !tour.isActive()) {
        // Mark done immediately so a mid-tour browser close doesn't replay
        localStorage.setItem(TOUR_KEY, "true");
        setTimeout(() => tour.start(), 500);
      }
    }

    window.addEventListener("goatflow:stake-done", startTour);

    fallbackTimer = setTimeout(() => {
      window.dispatchEvent(new CustomEvent("goatflow:stake-done"));
    }, 2000);

    return () => {
      window.removeEventListener("goatflow:stake-done", startTour);
      if (fallbackTimer) clearTimeout(fallbackTimer);
      if (tour.isActive()) tour.cancel();
    };
  }, []);

  return null;
}
