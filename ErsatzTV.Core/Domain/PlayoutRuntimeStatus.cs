namespace ErsatzTV.Core.Domain;

public enum PlayoutRuntimeStatus
{
    ActiveInTransmission = 0,
    ScheduledFuture = 1,
    OutOfPeriod = 2,
    Disabled = 3
}
