ALTER TABLE waitlist_leads
    DROP CONSTRAINT IF EXISTS waitlist_leads_locale_check;

ALTER TABLE waitlist_leads
    ADD CONSTRAINT waitlist_leads_locale_check CHECK (locale IN ('en', 'ru', 'zh', 'de', 'fr', 'es', 'ar'));
