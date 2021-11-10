from unittest import TestCase


def equal(possible_vals, single_val):
    for val in possible_vals:
        if single_val == val:
            return True
    return False


def within(possible_vals, container_val):
    for val in possible_vals:
        if val in container_val:
            return True
    return False


def container_of(possible_container_vals, single_val):
    for possible_container in possible_container_vals:
        if single_val in possible_container:
            return True
    return False


class _AnyEqualTest(TestCase):
    def test_any_equal_success(self):
        self.assertEqual(equal(["hi", "one", "is", "equal"], "equal"), True)

    def test_any_equal_fail(self):
        self.assertEqual(equal(["hi", "none", "are", "equal"], "not"), False)


class _AnyWithinTest(TestCase):
    def test_any_within_success(self):
        self.assertEqual(within(["hi", "one", "is", "equal"], "equality is key"), True)

    def test_any_within_fail(self):
        self.assertEqual(within(["hi", "none", "are", "equal"], "donkey"), False)


class _AnyContainerOfTest(TestCase):
    def test_any_container_of_success(self):
        possible_containers = ["monkey", "dunky", "is", "my", "friend"]
        self.assertEqual(container_of(possible_containers, "fri"), True)
        self.assertEqual(container_of(possible_containers, "dunk"), True)

    def test_any_container_of_fail(self):
        possible_containers = ["monkey", "dunky", "is", "my", "friend"]
        self.assertEqual(
            container_of(possible_containers, "theentirecommunistmanifesto"), False
        )
