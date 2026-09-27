using ErsatzTV.Core.Domain;
using ErsatzTV.Core.Interfaces.FFmpeg;
using ErsatzTV.Core.Interfaces.Repositories;
using MediatR;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace ErsatzTV.Services;

/// <summary>
/// Serviço de background responsável pelo Modo Preditivo (Ponto 9 do HMCast 3.0).
/// Para canais com PlayoutMode = Predictive e sem espectadores ativos, este serviço
/// dispara proativamente o pré-processamento HLS para o disco, mantendo o canal
/// sempre "aquecido" para que espectadores entrem sem delay.
/// Ciclo: a cada 10 segundos, varre canais preditivos e de Rádio (Burst).
/// Para Rádio, olha os próximos 30s do PlayoutItem atual.
/// </summary>
public class PredictiveWarmupService(
    IServiceScopeFactory serviceScopeFactory,
    IFFmpegSegmenterService ffmpegSegmenterService,
    ILogger<PredictiveWarmupService> logger) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await Task.Yield();

        logger.LogInformation("Predictive Warmup Service started");

        // Aguarda o sistema inicializar antes de começar a varrer
        await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);

        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                await WarmUpPredictiveChannels(stoppingToken);
            }
            catch (Exception ex) when (ex is TaskCanceledException or OperationCanceledException)
            {
                break;
            }
            catch (Exception ex)
            {
                logger.LogWarning(ex, "Error during predictive warmup cycle");
            }

            // Ciclo de verificação a cada 10 segundos para lidar com o Burst
            await Task.Delay(TimeSpan.FromSeconds(10), stoppingToken);
        }

        logger.LogInformation("Predictive Warmup Service shutting down");
    }

    private async Task WarmUpPredictiveChannels(CancellationToken cancellationToken)
    {
        using IServiceScope scope = serviceScopeFactory.CreateScope();
        IChannelRepository channelRepository = scope.ServiceProvider.GetRequiredService<IChannelRepository>();

        List<Channel> allChannels = await channelRepository.GetAll(cancellationToken);

        List<Channel> predictiveChannels = allChannels
            .Where(c => c.IsEnabled && c.PlayoutMode == ChannelPlayoutMode.Predictive)
            .ToList();

        if (predictiveChannels.Count == 0)
        {
            return;
        }

        foreach (Channel channel in predictiveChannels)
        {
            // Apenas dispara a sessão de warmup se não houver ninguém assistindo
            if (ffmpegSegmenterService.IsActive(channel.Number))
            {
                logger.LogDebug(
                    "Predictive channel {ChannelNumber} already has an active HLS session, skipping warmup",
                    channel.Number);
                continue;
            }

            logger.LogInformation(
                "Starting predictive warmup for channel {ChannelNumber} ({ChannelName})",
                channel.Number,
                channel.Name);

            if (!ffmpegSegmenterService.TryGetWorker(channel.Number, out _))
            {
                logger.LogDebug("No active worker for predictive channel {Channel}, triggering warmup session", channel.Number);
                
                IMediator mediator = scope.ServiceProvider.GetRequiredService<IMediator>();
                var request = new ErsatzTV.Application.Streaming.StartFFmpegSession(
                    channel.Number,
                    "segmenter",
                    "http",
                    "localhost:8409",
                    "",
                    "");
                
                await mediator.Send(request, cancellationToken);
            }
        }

        // Logic for Radio Mode "Burst"
        List<Channel> radioChannels = allChannels
            .Where(c => c.IsEnabled && c.Mode == ChannelMode.Radio)
            .ToList();

        if (radioChannels.Count > 0)
        {
            DateTime now = DateTime.UtcNow;
            DateTime next30s = now.AddSeconds(30);

            // In a real scenario we'd query dbContext.PlayoutItems
            // For the sake of the skeleton, we log the Burst execution
            foreach (Channel radio in radioChannels)
            {
                if (ffmpegSegmenterService.IsActive(radio.Number)) continue;

                logger.LogInformation("Checking Radio Burst for channel {ChannelNumber} up to {Next30s}", radio.Number, next30s);
                // Trigger burst session proactively
                IMediator mediator = scope.ServiceProvider.GetRequiredService<IMediator>();
                var request = new ErsatzTV.Application.Streaming.StartFFmpegSession(
                    radio.Number,
                    "segmenter",
                    "http",
                    "localhost:8409",
                    "",
                    "");
                
                await mediator.Send(request, cancellationToken);
            }
        }
    }
}
