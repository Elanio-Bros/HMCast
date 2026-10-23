using System.Collections.Generic;

namespace ErsatzTV.Core.Domain;

public class ScreenLayoutElement
{
    public int Id { get; set; }
    public int ScreenLayoutId { get; set; }
    public ScreenLayout ScreenLayout { get; set; }

    public string Name { get; set; }
    public ScreenLayoutElementType ElementType { get; set; }
    public int ZIndex { get; set; }

    // Coordenadas e Dimensões Relativas/Pixels
    public double X { get; set; }
    public double Y { get; set; }
    public double Width { get; set; }
    public double Height { get; set; }
    public double Opacity { get; set; } = 1.0;

    // Conteúdo
    public string ContentPath { get; set; }
    public string TextContent { get; set; }

    // Animações
    public int FadeInMs { get; set; }
    public int FadeOutMs { get; set; }

    // Relacionamento Pai-Filho
    public int? ParentElementId { get; set; }
    public ScreenLayoutElement ParentElement { get; set; }
    public List<ScreenLayoutElement> ChildElements { get; set; } = new();
}
