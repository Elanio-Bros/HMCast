namespace ErsatzTV.Core.Domain;

public enum MediaSkipSource
{
    Manual      = 1,
    EDL         = 2,
    NFO         = 3,
    Jellyfin    = 4,
    Plex        = 5,
    Emby        = 6,
    Blackdetect = 7,
    Chapter     = 8,
    Bulk        = 9,
}
