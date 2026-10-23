namespace ErsatzTV.Core.Scheduling;

public enum FixedStartTimeBehavior
{
    WaitUntilNext = 0,
    CutOffCurrent = 1,
    Flexible = 2,
    Strict = 3
}
