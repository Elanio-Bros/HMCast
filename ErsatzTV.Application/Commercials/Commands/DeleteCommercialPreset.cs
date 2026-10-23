using MediatR;

namespace ErsatzTV.Application.Commercials;

public record DeleteCommercialPreset(int Id) : IRequest;
