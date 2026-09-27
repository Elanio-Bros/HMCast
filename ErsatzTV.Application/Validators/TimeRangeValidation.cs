using System;

namespace ErsatzTV.Application.Scheduling;

public static class TimeRangeValidation
{
    public static bool Intersects(TimeSpan start1, TimeSpan end1, TimeSpan start2, TimeSpan end2)
    {
        // normalize to single day start
        double s1 = start1.TotalDays % 1.0;
        double d1 = (end1 - start1).TotalDays;
        
        double s2 = start2.TotalDays % 1.0;
        double d2 = (end2 - start2).TotalDays;
        
        if (d1 <= 0 || d2 <= 0) return false;
        
        double e1 = s1 + d1;
        double e2 = s2 + d2;
        
        // Base case: normal overlap
        if (s1 < e2 && s2 < e1) return true;
        
        // Wrap case 1: interval 2 crosses midnight into interval 1's space
        if (s1 < e2 - 1 && s2 - 1 < e1) return true;
        
        // Wrap case 2: interval 1 crosses midnight into interval 2's space
        if (s1 - 1 < e2 && s2 < e1 - 1) return true;
        
        return false;
    }
}
