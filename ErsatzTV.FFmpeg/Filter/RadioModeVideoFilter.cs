using ErsatzTV.FFmpeg.Environment;

namespace ErsatzTV.FFmpeg.Filter;

/// <summary>
/// Filtro do Modo Rádio (Ponto 10 do HMCast 3.0).
/// Substitui o vídeo original por uma cor sólida preta a 1fps,
/// preservando apenas o áudio, reduzindo drasticamente o consumo de banda e CPU/GPU.
/// Resultado: transmissão cai de ~5 Mbps para ~128 kbps.
/// </summary>
public class RadioModeVideoFilter : BaseFilter
{
    /// <summary>
    /// Substitui o vídeo original por fundo preto estático de 1fps.
    /// O filtro "nullsrc" cria um frame vazio e "geq" o preenche com preto puro.
    /// </summary>
    public override string Filter => "color=c=black:size=128x72:rate=1[v]";

    public override string[] FilterOptions => ["-filter_complex", Filter, "-map", "[v]", "-map", "0:a"];

    public override FrameState NextState(FrameState currentState) => currentState with
    {
        VideoFormat = "rawvideo"
    };
}
