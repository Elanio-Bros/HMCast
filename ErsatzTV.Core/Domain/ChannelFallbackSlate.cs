namespace ErsatzTV.Core.Domain;

public class ChannelFallbackSlate
{
    public int Id { get; set; }

    // Vínculo 1-para-1 com o Canal
    public int ChannelId { get; set; }
    public Channel Channel { get; set; }

    // Modo de contingência
    public FallbackSlateMode Mode { get; set; }

    // Fontes possíveis (Princípio da Fonte Universal)
    public int? MediaItemId { get; set; }
    public MediaItem MediaItem { get; set; }

    public int? CollectionId { get; set; }
    public Collection Collection { get; set; }

    public int? PlaylistId { get; set; }
    public Playlist Playlist { get; set; }

    // Textos informativos opcionais de tela
    public string CustomTitle { get; set; }
    public string CustomMessage { get; set; }

    // Execução contínua
    public bool IsLoop { get; set; } = true;
}
