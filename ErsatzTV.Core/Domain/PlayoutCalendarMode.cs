namespace ErsatzTV.Core.Domain;

public enum PlayoutCalendarMode
{
    AlwaysActive = 0,
    SpecificDaysOfWeek = 1,
    DateRange = 2,
    RecurringAnnual = 3,
    CustomRules = 4
}
