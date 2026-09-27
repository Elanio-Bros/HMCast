using ErsatzTV.Core.Domain;
using ErsatzTV.FFmpeg.Filter;
using NUnit.Framework;
using Shouldly;

namespace ErsatzTV.Core.Tests.Scheduling;

[TestFixture]
public class RadioModeFilterTests
{
    [Test]
    public void RadioModeVideoFilter_Should_Use_Black_Color_Source()
    {
        var filter = new RadioModeVideoFilter();

        filter.FilterOptions.ShouldContain("-filter_complex");
        filter.Filter.ShouldContain("color=c=black");
    }

    [Test]
    public void RadioModeVideoFilter_Should_Use_Low_Framerate()
    {
        var filter = new RadioModeVideoFilter();

        // 1fps garante consumo mínimo de banda no vídeo
        filter.Filter.ShouldContain("rate=1");
    }

    [Test]
    public void RadioModeVideoFilter_Should_Map_Audio_Stream()
    {
        var filter = new RadioModeVideoFilter();

        // O filtro deve preservar o áudio original (0:a)
        filter.FilterOptions.ShouldContain("-map");
        filter.FilterOptions.ShouldContain("0:a");
    }

    [Test]
    public void Channel_Mode_Should_Default_To_Television()
    {
        var channel = new Channel(Guid.NewGuid());

        channel.Mode.ShouldBe(ChannelMode.Television);
    }

    [Test]
    public void Channel_Mode_Can_Be_Set_To_Radio()
    {
        var channel = new Channel(Guid.NewGuid()) { Mode = ChannelMode.Radio };

        channel.Mode.ShouldBe(ChannelMode.Radio);
    }
}
