using ErsatzTV.Core.Domain;
using NUnit.Framework;
using Shouldly;

namespace ErsatzTV.Core.Tests.Scheduling;

[TestFixture]
public class PredictiveModeTests
{
    [Test]
    public void ChannelPlayoutMode_Should_Contain_Predictive_Value()
    {
        var values = Enum.GetValues<ChannelPlayoutMode>();

        values.ShouldContain(ChannelPlayoutMode.Predictive);
    }

    [Test]
    public void Predictive_Should_Have_Value_2()
    {
        ((int)ChannelPlayoutMode.Predictive).ShouldBe(2);
    }

    [Test]
    public void Continuous_And_OnDemand_Should_Not_Be_Affected()
    {
        ((int)ChannelPlayoutMode.Continuous).ShouldBe(0);
        ((int)ChannelPlayoutMode.OnDemand).ShouldBe(1);
    }

    [Test]
    public void Channel_PlayoutMode_Defaults_To_Continuous()
    {
        // O canal novo não deve ser Preditivo por padrão
        var channel = new Channel(Guid.NewGuid());

        channel.PlayoutMode.ShouldNotBe(ChannelPlayoutMode.Predictive);
    }

    [Test]
    public void Channel_Can_Be_Set_To_Predictive_Mode()
    {
        var channel = new Channel(Guid.NewGuid())
        {
            PlayoutMode = ChannelPlayoutMode.Predictive
        };

        channel.PlayoutMode.ShouldBe(ChannelPlayoutMode.Predictive);
    }
}
