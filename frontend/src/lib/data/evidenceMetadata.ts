import { getCapturedAt } from '@/lib/data/captureTime';

// Everything the case board can learn about a piece of evidence from its exiftool metadata.

export type GeoPoint = { lat: number; lon: number; altitude?: number };

export type EvidenceFacts = {
    capturedAt: number | null;
    location: GeoPoint | null;
    heading: number | null;
    place: string | null;
    device: string | null;
    deviceKey: string | null;
    software: string | null;
    editNote: string | null;
};

type Meta = Record<string, unknown>;

function readMetadata(reportArtifacts: Record<string, unknown> | null | undefined): Meta {
    const metadata = reportArtifacts?.metadata;
    return metadata && typeof metadata === 'object' ? (metadata as Meta) : {};
}

const EMPTY = new Set(['', 'undef', 'unknown', 'none', 'n/a', '0000:00:00 00:00:00']);

// All values whose tag name (ignoring the "Group:" prefix) matches, in metadata order
function tagValues(meta: Meta, name: string): unknown[] {
    const out: unknown[] = [];
    for (const [key, value] of Object.entries(meta)) {
        const tag = key.split(':').pop() ?? key;
        if (tag.toLowerCase() === name) out.push(value);
    }
    return out;
}

function firstText(meta: Meta, names: string[], allowNumbers = false): string | null {
    for (const name of names) {
        for (const value of tagValues(meta, name)) {
            if (typeof value === 'string' && !EMPTY.has(value.trim().toLowerCase())) return value.trim();
            if (allowNumbers && typeof value === 'number' && Number.isFinite(value) && value !== 0) return String(value);
        }
    }
    return null;
}

function firstNumber(meta: Meta, names: string[]): number | null {
    for (const name of names) {
        for (const value of tagValues(meta, name)) {
            const num = typeof value === 'number' ? value : typeof value === 'string' ? Number.parseFloat(value) : NaN;
            if (Number.isFinite(num)) return num;
        }
    }
    return null;
}

// Location

// Accepts a signed number, a numeric string, or a DMS string like `25 deg 45' 2.40" S`
function toCoordinate(value: unknown, ref?: unknown): number | null {
    let num: number | null = null;
    let hemisphere = typeof ref === 'string' ? ref.trim().toUpperCase().charAt(0) : '';

    if (typeof value === 'number') {
        num = value;
    } else if (typeof value === 'string' && value.trim()) {
        const dms = value.match(/(-?\d+(?:\.\d+)?)\s*(?:deg|°)\s*(\d+(?:\.\d+)?)?'?\s*(\d+(?:\.\d+)?)?"?\s*([NSEW])?/i);
        if (dms) {
            const [, d, m = '0', s = '0', h] = dms;
            num = Math.abs(Number(d)) + Number(m) / 60 + Number(s) / 3600;
            if (Number(d) < 0) num = -num;
            if (h) hemisphere = h.toUpperCase();
        } else {
            const parsed = Number.parseFloat(value);
            num = Number.isFinite(parsed) ? parsed : null;
        }
    }
    if (num == null || !Number.isFinite(num)) return null;
    if (hemisphere === 'S' || hemisphere === 'W') num = -Math.abs(num);
    return num;
}

function validPoint(lat: number | null, lon: number | null, altitude?: number | null): GeoPoint | null {
    if (lat == null || lon == null) return null;
    if (Math.abs(lat) > 90 || Math.abs(lon) > 180) return null;
    if (lat === 0 && lon === 0) return null; // "null island" = GPS block present but empty
    return altitude != null && Number.isFinite(altitude) ? { lat, lon, altitude } : { lat, lon };
}

// "lat lon [alt]" (QuickTime with -n), "lat, lon", or ISO 6709 "+25.7479+028.2293+1350.000/"
function parseCoordinateString(value: unknown): GeoPoint | null {
    if (typeof value !== 'string') return null;
    const text = value.trim();
    const iso = text.match(/^([+-]\d+(?:\.\d+)?)([+-]\d+(?:\.\d+)?)([+-]\d+(?:\.\d+)?)?(?:CRS[^/]*)?\/?$/);
    if (iso) return validPoint(Number(iso[1]), Number(iso[2]), iso[3] != null ? Number(iso[3]) : null);

    const parts = text.split(/[\s,]+/).map(Number).filter(Number.isFinite);
    if (parts.length >= 2) return validPoint(parts[0], parts[1], parts[2] ?? null);
    return null;
}

export function getLocation(meta: Meta): GeoPoint | null {
    // Composite values are already signed
    const altitude = firstNumber(meta, ['gpsaltitude']);
    const altitudeRef = firstNumber(meta, ['gpsaltituderef']);
    const signedAltitude = altitude != null && altitudeRef === 1 ? -Math.abs(altitude) : altitude;

    const composite = validPoint(
        toCoordinate(meta['Composite:GPSLatitude']),
        toCoordinate(meta['Composite:GPSLongitude']),
        signedAltitude,
    );
    if (composite) return composite;

    // Raw EXIF values are unsigned and need their N/S/E/W reference
    for (const group of ['EXIF', 'XMP', 'GPS']) {
        const point = validPoint(
            toCoordinate(meta[`${group}:GPSLatitude`], meta[`${group}:GPSLatitudeRef`]),
            toCoordinate(meta[`${group}:GPSLongitude`], meta[`${group}:GPSLongitudeRef`]),
            signedAltitude,
        );
        if (point) return point;
    }

    // Videos and anything else that stores the position as one string
    for (const name of ['gpscoordinates', 'gpsposition', 'location-eng', 'locationinformation', 'location']) {
        for (const value of tagValues(meta, name)) {
            const point = parseCoordinateString(value);
            if (point) return point;
        }
    }
    return null;
}

function getHeading(meta: Meta): number | null {
    const heading = firstNumber(meta, ['gpsimgdirection', 'cameradirection']);
    return heading != null && heading >= 0 && heading <= 360 ? heading : null;
}

function getPlace(meta: Meta): string | null {
    const parts = [
        firstText(meta, ['sublocation', 'sub-location', 'location']),
        firstText(meta, ['geolocationcity', 'city']),
        firstText(meta, ['geolocationregion', 'state', 'province-state']),
        firstText(meta, ['geolocationcountry', 'country', 'country-primarylocationname']),
    ].filter((part): part is string => part != null && parseCoordinateString(part) == null);

    const unique = parts.filter((part, i) => parts.findIndex((p) => p.toLowerCase() === part.toLowerCase()) === i);
    return unique.length ? unique.slice(0, 3).join(', ') : null;
}

// Device

function getDevice(meta: Meta): { device: string | null; deviceKey: string | null } {
    const make = firstText(meta, ['make', 'androidmanufacturer']);
    const model = firstText(meta, ['model', 'androidmodel', 'cameramodelname']);
    const serial = firstText(meta, ['bodyserialnumber', 'serialnumber', 'internalserialnumber', 'cameraserialnumber'], true);

    if (!make && !model) return { device: null, deviceKey: null };

    const device = make && model
        ? model.toLowerCase().startsWith(make.toLowerCase()) ? model : `${make} ${model}`
        : (make ?? model)!;

    const deviceKey = device.toLowerCase().replace(/\s+/g, ' ') + (serial ? `#${serial.toLowerCase()}` : '');
    return { device, deviceKey };
}

// Editing signals

const EDITORS = /photoshop|lightroom|gimp|snapseed|picsart|canva|facetune|affinity|pixelmator|paint\.net|capture one|luminar|premiere|after effects|final cut|davinci|capcut|inshot|imovie|ffmpeg|lavf|handbrake/i;

function getSoftware(meta: Meta): string | null {
    return firstText(meta, ['software', 'creatortool', 'historysoftwareagent', 'encoder', 'writingapp']);
}

// Exif local time "YYYY:MM:DD HH:MM:SS" -> comparable ms (no timezone; only used for differences)
function exifLocalMs(value: unknown): number | null {
    if (typeof value !== 'string') return null;
    const m = value.match(/^(\d{4}):(\d{2}):(\d{2})[ T](\d{2}):(\d{2}):(\d{2})/);
    if (!m) return null;
    const ms = Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6]);
    return Number.isFinite(ms) ? ms : null;
}

function getEditNote(meta: Meta, software: string | null): string | null {
    if (software && EDITORS.test(software)) return `Processed with ${software}`;

    const original = exifLocalMs(meta['EXIF:DateTimeOriginal']);
    const modified = exifLocalMs(meta['EXIF:ModifyDate']);
    if (original != null && modified != null && modified - original > 60_000) {
        const minutes = Math.round((modified - original) / 60_000);
        const gap = minutes < 120 ? `${minutes} min` : minutes < 2880 ? `${Math.round(minutes / 60)} h` : `${Math.round(minutes / 1440)} days`;
        return `Modified ${gap} after capture`;
    }
    return null;
}

export function getEvidenceFacts(reportArtifacts: Record<string, unknown> | null | undefined): EvidenceFacts {
    const meta = readMetadata(reportArtifacts);
    const software = getSoftware(meta);
    return {
        capturedAt: getCapturedAt(reportArtifacts),
        location: getLocation(meta),
        heading: getHeading(meta),
        place: getPlace(meta),
        ...getDevice(meta),
        software,
        editNote: getEditNote(meta, software),
    };
}

// Evidence is worth placing on a generated board if we know when, where, or what captured it
export function hasBoardFacts(facts: EvidenceFacts): boolean {
    return facts.capturedAt != null || facts.location != null || facts.deviceKey != null;
}

// Great-circle distance in km
export function distanceKm(a: GeoPoint, b: GeoPoint): number {
    const rad = Math.PI / 180;
    const dLat = (b.lat - a.lat) * rad;
    const dLon = (b.lon - a.lon) * rad;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dLon / 2) ** 2;
    return 2 * 6371 * Math.asin(Math.min(1, Math.sqrt(h)));
}

export function formatKm(km: number): string {
    if (km < 1) return `${Math.round(km * 1000)} m`;
    return `${km < 10 ? km.toFixed(1) : Math.round(km).toLocaleString()} km`;
}

export function formatCoordinates(point: GeoPoint): string {
    return `${point.lat.toFixed(5)}, ${point.lon.toFixed(5)}`;
}

const COMPASS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];

// Short label for the board plus a fuller tooltip
export function describeLocation(facts: EvidenceFacts): { label: string; title: string } | null {
    if (!facts.location && !facts.place) return null;
    const coords = facts.location ? formatCoordinates(facts.location) : null;
    const extras = [
        coords,
        facts.location?.altitude != null ? `${Math.round(facts.location.altitude)} m altitude` : null,
        facts.heading != null ? `facing ${COMPASS[Math.round(facts.heading / 45) % 8]} (${Math.round(facts.heading)}°)` : null,
    ].filter(Boolean);
    return {
        label: facts.place ?? coords!,
        title: [facts.place, ...extras].filter(Boolean).join(' · '),
    };
}
