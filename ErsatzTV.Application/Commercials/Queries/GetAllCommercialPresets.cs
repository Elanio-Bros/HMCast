using System.Collections.Generic;
using MediatR;

namespace ErsatzTV.Application.Commercials;

public record GetAllCommercialPresets : IRequest<List<CommercialPresetViewModel>>;
