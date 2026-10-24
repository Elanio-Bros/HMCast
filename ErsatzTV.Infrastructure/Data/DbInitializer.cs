using System.Globalization;
using System.Reflection;
using Dapper;
using ErsatzTV.Core.Domain;

namespace ErsatzTV.Infrastructure.Data;

public static class DbInitializer
{
    public static async Task<Unit> Initialize(TvContext context, CancellationToken cancellationToken)
    {
        if (TvContext.IsSqlite)
        {
            await context.Connection.ExecuteAsync("PRAGMA journal_mode=WAL", cancellationToken);
        }
        else
        {
            int localInfile = await context.Connection.ExecuteScalarAsync<int>(
                "SELECT @@GLOBAL.local_infile");

            if (localInfile == 0)
            {
                try
                {
                    await context.Connection.ExecuteAsync("SET GLOBAL local_infile = 'ON'", cancellationToken);
                }
                catch
                {
                    Serilog.Log.Fatal(
                        """
                        ErsatzTV requires local_infile=ON when using MySQL.
                        Please run the following as a MySQL administrator:
                          SET GLOBAL local_infile = 'ON';
                        Or configure it in my.cnf under [mysqld].
                        """);
                    throw;
                }
            }
        }

        if (!context.LanguageCodes.Any())
        {
            var assembly = Assembly.GetEntryAssembly();
            if (assembly != null)
            {
                await using Stream resource =
                    assembly.GetManifestResourceStream("ErsatzTV.Resources.ISO-639-2_utf-8.txt");
                if (resource != null)
                {
                    using var reader = new StreamReader(resource);
                    string line;
                    while ((line = await reader.ReadLineAsync(cancellationToken)) is not null)
                    {
                        string[] split = line.Split("|");
                        if (split.Length == 5)
                        {
                            var languageCode = new LanguageCode
                            {
                                ThreeCode1 = split[0],
                                ThreeCode2 = split[1],
                                TwoCode = split[2],
                                EnglishName = split[3],
                                FrenchName = split[4]
                            };

                            await context.LanguageCodes.AddAsync(languageCode, cancellationToken);
                        }
                    }
                }
            }

            await context.SaveChangesAsync(cancellationToken);
        }

        var standardResolutions = new List<(string Name, int Width, int Height)>
        {
            ("720x480", 720, 480),
            ("1280x720", 1280, 720),
            ("1920x1080", 1920, 1080),
            ("3840x2160", 3840, 2160),
            ("640x360", 640, 360)
        };

        foreach (var (name, width, height) in standardResolutions)
        {
            if (!context.Resolutions.Any(r => r.Width == width && r.Height == height))
            {
                var res = new Resolution { Name = name, Width = width, Height = height };
                await context.Resolutions.AddAsync(res, cancellationToken);
            }
        }
        await context.SaveChangesAsync(cancellationToken);

        Resolution res1080 = context.Resolutions.FirstOrDefault(r => r.Width == 1920 && r.Height == 1080)
            ?? context.Resolutions.First();
        Resolution res720 = context.Resolutions.FirstOrDefault(r => r.Width == 1280 && r.Height == 720)
            ?? res1080;
        Resolution res480 = context.Resolutions.FirstOrDefault(r => r.Width == 720 && r.Height == 480)
            ?? res1080;
        Resolution res360 = context.Resolutions.FirstOrDefault(r => r.Width == 640 && r.Height == 360)
            ?? res480;

        if (!context.ConfigElements.Any(c => c.Key == ConfigElementKey.FFmpegDefaultResolutionId.Key))
        {
            var resolutionConfig = new ConfigElement
            {
                Key = ConfigElementKey.FFmpegDefaultResolutionId.Key,
                Value = res1080.Id.ToString(CultureInfo.InvariantCulture)
            };
            await context.ConfigElements.AddAsync(resolutionConfig, cancellationToken);
            await context.SaveChangesAsync(cancellationToken);
        }

        // HMCast 3.0: 4 Perfis Factory Idempotentes
        var fhdProfile = context.FFmpegProfiles.FirstOrDefault(p => p.Name == "1080p FHD");
        if (fhdProfile == null)
        {
            fhdProfile = FFmpegProfile.New("1080p FHD", res1080);
            fhdProfile.VideoBitrate = 4500;
            fhdProfile.VideoBufferSize = 9000;
            fhdProfile.AudioBitrate = 192;
            fhdProfile.AudioBufferSize = 384;
            await context.FFmpegProfiles.AddAsync(fhdProfile, cancellationToken);
        }

        if (!context.FFmpegProfiles.Any(p => p.Name == "720p HD"))
        {
            var profile720 = FFmpegProfile.New("720p HD", res720);
            profile720.VideoBitrate = 2500;
            profile720.VideoBufferSize = 5000;
            profile720.AudioBitrate = 192;
            profile720.AudioBufferSize = 384;
            await context.FFmpegProfiles.AddAsync(profile720, cancellationToken);
        }

        if (!context.FFmpegProfiles.Any(p => p.Name == "480p SD"))
        {
            var profile480 = FFmpegProfile.New("480p SD", res480);
            profile480.VideoBitrate = 1200;
            profile480.VideoBufferSize = 2400;
            profile480.AudioBitrate = 128;
            profile480.AudioBufferSize = 256;
            await context.FFmpegProfiles.AddAsync(profile480, cancellationToken);
        }

        if (!context.FFmpegProfiles.Any(p => p.Name == "Rádio Web"))
        {
            var radioProfile = FFmpegProfile.New("Rádio Web", res360);
            radioProfile.VideoBitrate = 64;
            radioProfile.VideoBufferSize = 128;
            radioProfile.AudioBitrate = 192;
            radioProfile.AudioBufferSize = 384;
            await context.FFmpegProfiles.AddAsync(radioProfile, cancellationToken);
        }

        await context.SaveChangesAsync(cancellationToken);

        if (!context.ConfigElements.Any(c => c.Key == ConfigElementKey.FFmpegDefaultProfileId.Key))
        {
            var profileConfig = new ConfigElement
            {
                Key = ConfigElementKey.FFmpegDefaultProfileId.Key,
                Value = fhdProfile.Id.ToString(CultureInfo.InvariantCulture)
            };
            await context.ConfigElements.AddAsync(profileConfig, cancellationToken);
            await context.SaveChangesAsync(cancellationToken);
        }

        // Canal Padrão HMCast
        if (!context.Channels.Any())
        {
            var defaultChannel = new Channel(Guid.NewGuid())
            {
                Number = "1",
                Name = "HMCast",
                FFmpegProfile = fhdProfile,
                StreamingEngine = StreamingEngine.Next,
                StreamingMode = StreamingMode.TransportStreamHybrid,
                IsEnabled = true,
                ShowInEpg = true
            };
            await context.Channels.AddAsync(defaultChannel, cancellationToken);
            await context.SaveChangesAsync(cancellationToken);
        }
        else
        {
            var ersatzChannel = context.Channels.FirstOrDefault(c => c.Name == "ErsatzTV");
            if (ersatzChannel != null)
            {
                ersatzChannel.Name = "HMCast";
                await context.SaveChangesAsync(cancellationToken);
            }
        }

        return Unit.Default;
    }
}
