/**
 * Navigation param types for type-safe navigation.
 * Define once, reuse everywhere to prevent mismatches.
 */
export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
};

export type TabParamList = {
  Log: undefined;
  History: undefined;
  Coach: undefined;
  Profile: undefined;
};

/** Main app stack when authenticated: tabs + VerifyEmail + Weekly Report + Timeline + Plan Details (Phase 2 Week 7). */
export type MainStackParamList = {
  MainTabs: undefined;
  VerifyEmail: undefined;
  WeeklyReport: undefined;
  TimelineDetails: undefined;
  PlanDetails: undefined;
};

/** History tab stack: list, workout detail, Progress & Trends, Insights (Phase 3). */
export type HistoryStackParamList = {
  HistoryList: undefined;
  WorkoutDetail: { workoutId: string };
  ProgressTrends: undefined;
  Insights: undefined;
};

// Re-export for convenience
export type RootStackParamList = AuthStackParamList & TabParamList & MainStackParamList;
