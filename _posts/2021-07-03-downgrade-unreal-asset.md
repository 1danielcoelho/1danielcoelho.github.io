---
layout: post
title: How to downgrade Unreal Engine assets
tags: unreal
description: How to move an asset from a newer UnrealEngine version to an older one
---

You try updating your project to a newer Unreal Engine version, play around for a bit and realize you need to revert to a previous version. You already changed and resaved some of your assets though, what can you do?

I couldn't find a solution to this after a quick search, but I've used a hack for this before that could be useful. Note that this is sort of a "last resort", and should almost always be a bad idea.

> DISCLAIMER: Please make sure you backup your assets somewhere else before trying this, as this hack could permanently destroy them! 

## The problem

For this sample I'll move a static mesh asset that was saved in 4.27 Preview 2 down to 4.26.2, but this should work for any pair of UE4/5 versions. You'll get into more trouble the further apart the engine versions are, though.

Anyway, if I just try opening the asset saved in 4.27P2 with my 4.26.2 engine and project, I get an error that looks like this:
```
LogAssetRegistry: Error: Package E:/Unreal projects/Test_426/Content/BlenderCube.uasset has newer custom version of Dev-Rendering
```

## The cause

What is a `Dev-Rendering`? Check [DevObjectVersion.cpp](https://github.com/EpicGames/UnrealEngine/blob/c3caf7b6bf12ae4c8e09b606f10a09776b4d1f38/Engine/Source/Runtime/Core/Private/UObject/DevObjectVersion.cpp#L110). The relevant snippet looks like this:

``` C++ 
// Unique Rendering Object version id
const FGuid FRenderingObjectVersion::GUID(0x12F88B9F, 0x88754AFC, 0xA67CD90C, 0x383ABD29);
// Register Rendering custom version with Core
FDevVersionRegistration GRegisterRenderingObjectVersion(FRenderingObjectVersion::GUID, FRenderingObjectVersion::LatestVersion, TEXT("Dev-Rendering"));
```

Here is the start and end of that [`FRenderingObjectVersion` enum](https://github.com/EpicGames/UnrealEngine/blob/c3caf7b6bf12ae4c8e09b606f10a09776b4d1f38/Engine/Source/Runtime/Core/Public/UObject/RenderingObjectVersion.h#L8):

``` C++
// Custom serialization version for changes made in Dev-Rendering stream
struct CORE_API FRenderingObjectVersion
{
	enum Type
	{
		// Before any version changes were made
		BeforeCustomVersionWasAdded = 0,

		// Added support for 3 band SH in the ILC
		IndirectLightingCache3BandSupport,

		// Allows specifying resolution for reflection capture probes
		CustomReflectionCaptureResolutionSupport,

		RemovedTextureStreamingLevelData,

		... // Lots more

		// Remap Volume Extinction material input to RGB
		VolumeExtinctionBecomesRGB,

		// -----<new versions can be added above this line>-------------------------------------------------
		VersionPlusOne,
		LatestVersion = VersionPlusOne - 1
	};

	// The GUID for this custom version number
	const static FGuid GUID;

private:
	FRenderingObjectVersion() {}
};
```

This enum works like a version tracker for the `Dev-Rendering` "custom version". The idea is that they can have entries in that enum that correspond to changes that affect serialized assets. 

Saved uassets (static meshes, materials, even levels) can get serialized with that GUID we saw before (`0x12F88B9F, 0x88754AFC, 0xA67CD90C, 0x383ABD29`, which identifies `Dev-Rendering`), and the current value of `FRenderingObjectVersion::LastVersion`, which means the asset requires this particular version (or later) of the `Dev-Rendering` custom version.

Whenever the asset is deserialized, what it thinks the value for `FRenderingObjectVersion::LastVersion` is is retrieved from the file and compared with the engine's own value for `FRenderingObjectVersion::LastVersion`. 

If the asset has a lower value for `LastVersion`, it means it was saved with an older engine version (that had less entries in that enum). This is usually not an issue though, because developers can write code on `UObject::Serialize(FArchive& Ar)` overloads that can automatically upgrade the older asset to the current engine version upon loading, since they know what the serialized representation looked like before and what it should look like now. 

If the asset has a higher number for `LastVersion`, it means that the enum had more entries when the asset was saved, i.e. the asset was saved with a newer engine version. The developers can't do much about that unfortunately: The way the asset is represented on disk can have arbitrarily changed in some way our engine doesn't understand yet, so the loading is aborted.

You can see where this is going: It's pretty risky to try this if you're trying to downgrade a material and the version for `Dev-Rendering` changed, but it shouldn't be *impossible* to manually downgrade something like a static mesh if only the version of `FortniteRelease` changed, or something like that. Likely our mesh doesn't have any Fortnite data stored in it, so it's serialized representation on disk probably hasn't changed much even though `FortniteRelease` has. Luckily these GUIDs and values are stored uncompressed/unhashed on the asset files, so we can do something about it. 

## The workaround

These version numbers can be tweaked on the assets directly. Here is what the start of that `BlenderCube.uasset` asset looks like on a hex editor. It doesn't matter what asset (or asset type) it is, this "file header" should always have more or less the same structure. 

[![Dev-Rendering GUID with 2D value](/assets/images/downgrade-unreal-asset/dev-rendering-2d.png)](/assets/images/downgrade-unreal-asset/dev-rendering-2d.png)

This header corresponds to a serialized [`FPackageFileSummary`](https://github.com/EpicGames/UnrealEngine/blob/c3caf7b6bf12ae4c8e09b606f10a09776b4d1f38/Engine/Source/Runtime/CoreUObject/Public/UObject/PackageFileSummary.h#L46) by the way, and you can see the serialization process [here](https://github.com/EpicGames/UnrealEngine/blob/c3caf7b6bf12ae4c8e09b606f10a09776b4d1f38/Engine/Source/Runtime/CoreUObject/Private/UObject/PackageFileSummary.cpp#L48).

Anyway, the highlighted bit is our `Dev-Rendering` GUID, except that it was serialized as [little endian](https://en.wikipedia.org/wiki/Endianness#/media/File:Little-Endian.svg). TL;DR: It will be written to disk inverting the order of bytes (pair of characters) in each of the values in the GUID, so the first group `0x12F88B9F`, which has the bytes `12 F8 8B 9F`, becomes `9F 8B F8 12`, which is the start of the highlighted text on that image.

The value in red right after the GUID is the current value for the `Dev-Rendering` enum: `0000002D`, which is hexadecimal for 45. Our asset was saved with `FRenderingObjectVersion::LastVersion = 45`.

If you just switch between the 4.27 and 4.26 branches on [the file of the enum's declaration](https://github.com/EpicGames/UnrealEngine/blob/4.27/Engine/Source/Runtime/Core/Public/UObject/RenderingObjectVersion.h) you can see that it has gained a new entry in 4.27: `VolumeExtinctionBecomesRGB`. This means that in 4.26, `LastVersion` was probably just 44, which is `2C`. We can just write `2C` there and save:

[![Dev-Rendering GUID with 2C value](/assets/images/downgrade-unreal-asset/dev-rendering-2c.png)](/assets/images/downgrade-unreal-asset/dev-rendering-2c.png)

This should do it. Realistically though, not just `Dev-Rendering` will change between engine versions, and you'd have to repeat this about 5-10 times for different enums. 

## The faster workaround

I made [a small Python 3 script](/assets/images/downgrade-unreal-asset/downgrade_uasset.py) that should help with the tediousness of this, though. It will make sure that e.g. the value for `Dev-Rendering` is *at most* the one that you set it. It has all the custom versions listed on [DevObjectVersion.cpp](https://github.com/EpicGames/UnrealEngine/blob/c3caf7b6bf12ae4c8e09b606f10a09776b4d1f38/Engine/Source/Runtime/Core/Private/UObject/DevObjectVersion.cpp#L110) plus the `Release` custom version, but you may need to manually add others that fit your cases, as individual plugins may also define their own custom version.

Hopefully the script is self-explanatory: The idea is to watch the UE Output Log for errors like we originally saw:
```
LogAssetRegistry: Error: Package E:/Unreal projects/Test_426/Content/BlenderCube.uasset has newer custom version of Dev-Rendering
```
Then add entries for those custom versions (here, `Dev-Rendering` again) with the `-1` value within the script's `updated_values` dict to probe what the value currently is. The script will output something like `Read 'Dev-Rendering' with value '45'`. Knowing that, you can change the `-1` value to `44` and run the script again to downgrade it to `44` instead. Once you run the script the file will be saved and UE will try loading it again, potentially outputting another error like custom version mismatch for `FortniteMain`. Repeat until it stops complaining. 

## The complete workaround

I've used this a couple times before and it works fine, and it should at least always get your asset to show up on the Content Browser. This is all you need if you're working on UE source and want to downgrade between different changelists, and your build version is still compatible with the asset. 

If you are moving an asset between different major/minor versions though (like we are doing here by moving it from 4.27P2 to 4.26.2), then we need one extra step. 

After you run the script (or did the version changes manually), the asset will show up on the Content Browser. If you double-click the asset though, you'll get a warning like this on the Output Log:

```
LogLinker: Warning: Asset 'E:/Unreal projects/Test_426/Content/BlenderCube.uasset' has been saved with a newer engine and can't be loaded. CurrentEngineVersion: 4.26.2-15973114+++UE4+Release-4.26 (Licensee=0). AssetEngineVersion: 4.27.0-16724560+++UE4+Release-4.27 (Licensee=0)
```

The major/minor versions, engine and compatible changelists and Perforce stream names are also saved on the asset, and the engine is trying it's best to prevent us from loading it (as it should, as this is a pretty bad idea in general!). 

Because of this we need to provide the major/minor/changelist versions to the script as well, so that it can replace that for us. In our case, from that error message we can tell that our asset has `major=4`, `minor=27`, `changelist=16724560`, and our engine has `major=4`, `minor=26` and `changelist=15973114`. On the script, set `update_engine_version` to `True` after you set these values on the variables defined right after it, and then run it. 

This is it, for real this time! If you can double-click now make sure you save your asset as soon as you can, so that it can be serialized correctly to disk by the engine, hopefully ironing out any small details we could have missed. 

If this doesn't work for you and your asset just crashes when opening, you may be in deeper trouble unfortunately. The versions could be far enough apart that the serialized representation of your asset changed on disk in some non-trivial way. It's probably not worth it to try and make sense of it, and you should just try recreating/reimporting your asset instead (or find an even crazier hack :) ).

