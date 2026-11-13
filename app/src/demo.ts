// Set at build time for the hosted demo (EXPO_PUBLIC_DEMO=1). The local research build leaves it unset.
export const DEMO = process.env.EXPO_PUBLIC_DEMO === '1';

export const DEMO_NOTICE = 'Public demo for supervisors and markers. Not part of the study.';

export const DEMO_PRIVACY =
  'This is a public demo, not part of the research study. What you enter is stored on the demo server only until '
  + 'it restarts (after about 15 minutes without visitors), is never used as study data, and you can delete it at any '
  + 'time in Settings. No tracking or analytics services are used. Please use a made-up or example CV.';
