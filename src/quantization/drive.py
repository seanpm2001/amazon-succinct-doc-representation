"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
# Taken from 'DRIVE: One-bit Distributed Mean Estimation' paper
from functools import lru_cache

import torch

import src.quantization.rotated_quantization as rotations
from src.quantization.transform import Transform


def gen_expected_normal_centroids_and_boundaries():
    # half-normal centroids
    k_bits_pos_centroids = {1: [0.7978845608028654],
                            2: [0.452780034636492, 1.5104176084990955],
                            3: [0.24509417894422167, 0.7560052812058773, 1.343909278505, 2.1519457045369874],
                            4: [0.128395029851147, 0.3880482994902902, 0.6567591185324634, 0.9423404564869614, 1.2562311973471771, 1.6180463860218826, 2.0690172265313866, 2.732589570995163],
                            5: [0.06588965977082256, 0.19805182966943216, 0.3313783057601116, 0.46669952297668094, 0.6049336240094318, 0.7471357036878163, 0.8945651173883715, 1.0487833199231986, 1.211804380609264, 1.3863403395866256, 1.5762280786121903, 1.7872332177032693, 2.028728399395497, 2.317739404194735, 2.6911195773766687, 3.2607324934014006],
                            6: [0.03340950637010074, 0.10027828930388713, 0.16729690336899547, 0.2345669853360093, 0.302192846371696, 0.370282645258938, 0.4389496716586352, 0.5083137808979938, 0.5785030305188004, 0.6496555810635404, 0.7219219405696736, 0.7954676558408593, 0.870476586544118, 0.9471549447432923, 1.0257363490773348, 1.1064882395373279, 1.1897201418608732, 1.2757944864337445, 1.3651410198102165, 1.4582763746978018, 1.5558312247051407, 1.6585889004238565, 1.767541882991204, 1.8839772405224506, 2.0096110425936944, 2.1468102170558803, 2.2989812097603872, 2.4713047976182803, 2.672273835255278, 2.917406790723003, 3.240437055012211, 3.744101270895345],
                            7: [0.016828169457257337, 0.05049086396324786, 0.08417264205883766, 0.1178862823031159, 0.15164464790978896, 0.1854607214256451, 0.21934764023847636, 0.2533187331700954, 0.2873875584246195, 0.32156794318058946, 0.35587402513815714, 0.39032029636002186, 0.42492164977766744, 0.45969342877351715, 0.4946514802958468, 0.5298122120178267, 0.56519265411632, 0.6008105263217581, 0.6366843109796396, 0.6728333329695212, 0.7092778474519102, 0.7460391365610942, 0.7831396163374086, 0.8206029554016402, 0.8584542071245348, 0.8967199573449002, 0.935428490052102, 0.9746099738874292, 1.0142966728523577, 1.0545231852638806, 1.0953267157982172, 1.1367473864538342, 1.1788285934942129, 1.2216174189677063, 1.265165107335604, 1.3095276201894268, 1.3547662851652738, 1.4009485591850843, 1.4481489313717788, 1.4964499978133121, 1.5459437493733037, 1.596733125792029, 1.6489339055840169, 1.7026770234583626, 1.7581114377453317, 1.8154077134957767, 1.8747625484931847, 1.9364045587161332, 2.000601771738897, 2.0676714756109984, 2.1379933780433253, 2.212027517525366, 2.2903391620216333, 2.373634269839721, 2.462811433129822, 2.5590405215205165, 2.6638865386312016, 2.7795142579810537, 2.9090470736096363, 3.0572461506081066, 3.231933204266534, 3.447430271103957, 3.7349366443632643, 4.189694156733378],
                            8: [0.008446193222756295, 0.025339383099345594, 0.042234983804242794, 0.05913460434083632, 0.07603985639252604, 0.0929523554012122, 0.10987372165229412, 0.12680558136807535, 0.1437495678114996, 0.16070732240217558, 0.17768049584669052, 0.19467074928525907, 0.21167975545680925, 0.22870919988466995, 0.24576078208509358, 0.2628362168009263, 0.27993723526282477, 0.2970655864805145, 0.3142230385666894, 0.33141138009626975, 0.3486324215038598, 0.3658879965223876, 0.38317996366605755, 0.4005102077609124, 0.41788064152647963, 0.43529320721217035, 0.45274987829231145, 0.47025266122391923, 0.4878035972715734, 0.5054047644040176, 0.5230582792674087, 0.5407662992404536, 0.5585310245770181, 0.5763547006421683, 0.5942396202480124, 0.6121881260961544, 0.6302026133340553, 0.6482855322331184, 0.6664393909968923, 0.6846667587084027, 0.7029702684263094, 0.7213526204403216, 0.7398165856971156, 0.7583650094088884, 0.7770008148576407, 0.795727007409354, 0.8145466787533798, 0.8334630113836405, 0.8524792833396407, 0.8715988732268272, 0.8908252655375329, 0.9101620562956106, 0.9296129590499155, 0.9491818112440852, 0.968872580992572, 0.9886893742956772, 1.0086364427294274, 1.0287181916495645, 1.048939188952738, 1.0693041744422376, 1.0898180698503408, 1.110485989574644, 1.13131325219166, 1.1523053928175975, 1.1734681763936767, 1.1948076119816973, 1.2163299681649922, 1.2380417896605218, 1.2599499152598737, 1.2820614972305167, 1.3043840223240994, 1.3269253345561072, 1.349693659941183, 1.3726976333912353, 1.3959463280095736, 1.4194492870442756, 1.4432165587984476, 1.4672587348347692, 1.4915869918576432, 1.5162131377095, 1.5411496619796943, 1.5664097917965718, 1.5920075534576597, 1.6179578406518962, 1.6442764901443314, 1.6709803659313192, 1.6980874530373322, 1.7256169623186122, 1.753589447870698, 1.7820269389149666, 1.810953088374312, 1.8403933407534958, 1.8703751224326286, 1.900928058084589, 1.93208421766716, 1.9638783993546949, 1.99634845490986, 2.029535665415902, 2.063485177076778, 2.09824650905685, 2.133874148222555, 2.1704282493679052, 2.2079754643316654, 2.246589929732332, 2.2863544513987355, 2.327361934728369, 2.36971712526939, 2.4135387444120555, 2.458962133587387, 2.5061425604170537, 2.5552593973824385, 2.6065214664607876, 2.6601739656957775, 2.71650757857875, 2.775870652699903, 2.8386857867574364, 2.90547290366505, 2.976882133701405, 3.0537420161692928, 3.1371325317023246, 3.2285002105788148, 3.329848470000476, 3.4440716782142333, 3.5755879723915944, 3.7316662622241643, 3.9256377839361196, 4.186595442844834, 4.603535612430344]}

    # normal centroids (added symmetric negative values)
    k_bits_centroids = dict(zip(
        k_bits_pos_centroids.keys(),
        [[-c for c in reversed(pos_centroids)] + pos_centroids for pos_centroids in k_bits_pos_centroids.values()]
    ))

    k_bits_boundaries = dict(zip(
        k_bits_centroids.keys(),
        [[(a + b) / 2 for a, b in zip(centroids[:-1], centroids[1:])] for centroids in k_bits_centroids.values()]
    ))

    return k_bits_centroids, k_bits_boundaries


e_centroids, e_boundaries = gen_expected_normal_centroids_and_boundaries()


@lru_cache(maxsize=None)  # TODO use functools.cache in python 3.9
def e_centroids_tensor(bits, device):
    return torch.Tensor(e_centroids[bits]).to(device)


@lru_cache(maxsize=None)  # TODO use functools.cache in python 3.9
def e_boundaries_tensor(bits, device):
    return torch.Tensor(e_boundaries[bits]).to(device)


def l1(x, op_kwargs):
    return torch.sum(torch.abs(x), **op_kwargs)


def sum_squares(x, op_kwargs):
    return torch.sum(x ** 2, **op_kwargs)


def l2(x, op_kwargs):
    return torch.sqrt(sum_squares(x, op_kwargs))


def normal_kmeans_assignments(x, vec_dim, bits, op_kwargs):
    scale = (vec_dim ** 0.5) / l2(x, op_kwargs)

    boundaries = e_boundaries_tensor(bits, x.device)
    assignments = torch.bucketize(x * scale, boundaries)

    return assignments


class DriveClusteringStage(Transform):
    def __init__(self, bits, bias_correction=True, std_outlier_factor=None, batched=False):
        self.bits = bits
        self.bias_correction = bias_correction
        self.std_outlier_factor = std_outlier_factor
        if batched:
            self.op_kwargs = {"dim": 1, "keepdim": True}
            self.vec_dim = lambda x: x.shape[1]
        else:
            self.op_kwargs = {}
            self.vec_dim = lambda x: x.numel()

    def forward(self, x):
        if self.std_outlier_factor is not None:
            mean, std = x.mean(**self.op_kwargs), x.std(**self.op_kwargs)
            # clamp with tensor inputs only supported on pytorch>=1.9
            # (so you need pytorch>=1.9 to work with batched vectors mode + std_outlier_factor
            x = x.clamp(mean - self.std_outlier_factor * std, mean + self.std_outlier_factor * std)

        if self.bits == 1:
            # just keeping this to check that 1 bit implementation produces the same results as kb with k=1
            if self.bias_correction:
                scale = sum_squares(x, self.op_kwargs) / l1(x, self.op_kwargs)
            else:
                scale = l1(x, self.op_kwargs) / self.vec_dim(x)
            return torch.ge(x, 0), scale

        assignments = normal_kmeans_assignments(x, self.vec_dim(x), self.bits, self.op_kwargs)

        if self.bias_correction:
            unscaled_kmeans_vec = torch.take(e_centroids_tensor(self.bits, x.device), assignments)

            scale = (l2(x, self.op_kwargs) * (self.vec_dim(x) ** 0.5)) / sum_squares(unscaled_kmeans_vec, self.op_kwargs)
        else:
            scale = l2(x, self.op_kwargs) * (self.vec_dim(x) ** -0.5)

        return assignments, scale

    def backward(self, f_res):
        assignments, scale = f_res

        if self.bits == 1:
            return (assignments * 2 - 1) * scale

        unscaled_kmeans_vec = torch.take(e_centroids_tensor(self.bits, assignments.device), assignments)

        # restore scale
        return scale * unscaled_kmeans_vec


class Drive(rotations.RotatedQuantization):
    def __init__(self, gen_seed, bits, bias_correction=True, std_outlier_factor=None, batched=False):
        super().__init__(
            pre_rotation_flat_and_pad=not batched,
            rotation=rotations.RandomizedHadamard(gen_seed, batched),
            post_rotation_transform=DriveClusteringStage(bits, bias_correction, std_outlier_factor, batched),
        )
